import sys
import os
import time
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from .models import TextImprovement, ToolUsageStats

# Add the ai_writing_assistant directory to Python path
ai_assistant_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'ai_writing_assistant')
sys.path.append(ai_assistant_path)

# Import the new LangGraph-based AI writing assistant
from langgraph_agent import LangGraphWritingAgent


class WritingAssistantService:
    """Service class to integrate LangGraph AI Writing Assistant with Django."""

    def __init__(self):
        # Initialize the LangGraph agent
        # You can set your Groq API key here or in environment variable
        self.agent = LangGraphWritingAgent()

    def process_text(self, text, specific_tools=None, tone=None):
        """Process text with the LangGraph AI agent and return results."""
        start_time = time.time()

        # Convert tool names from Django format to LangChain format
        tool_mapping = {
            'grammar_corrector': 'grammar_correction_tool',
            'sentence_rewriter': 'sentence_rewriting_tool',
            'vocabulary_enhancer': 'vocabulary_enhancement_tool',
            'tone_adjuster': 'tone_adjustment_tool'
        }

        # Map specific tools if provided
        mapped_tools = None
        if specific_tools:
            mapped_tools = [tool_mapping.get(tool, tool) for tool in specific_tools]

        # Use the LangGraph agent to improve text
        result = self.agent.improve_text(
            text=text,
            specific_tools=mapped_tools,
            tone=tone
        )

        # Calculate processing time
        processing_time = time.time() - start_time
        result['processing_time'] = processing_time

        # Format improvements for compatibility with existing frontend
        if result.get('success'):
            formatted_improvements = []
            for improvement in result.get('improvements', []):
                formatted_improvements.append({
                    'tool': improvement.get('tool', ''),
                    'before': text,  # Original text
                    'after': improvement.get('output', text),  # Tool output
                    'analysis': {}
                })
            result['improvements'] = formatted_improvements

        return result


# Global service instance
writing_service = WritingAssistantService()


def index(request):
    """Main page with writing assistant interface."""
    recent_improvements = TextImprovement.objects.all()[:5]
    context = {
        'recent_improvements': recent_improvements,
        'available_tools': writing_service.agent.get_available_tools(),
    }
    return render(request, 'writing_assistant/index.html', context)


@csrf_exempt
@require_http_methods(["POST"])
def improve_text(request):
    """API endpoint to improve text using the AI agent."""
    try:
        text = request.POST.get('text', '').strip()
        specific_tools = request.POST.getlist('tools')
        tone = request.POST.get('tone', '').strip()

        if not text:
            return JsonResponse({'error': 'No text provided'}, status=400)

        # Process text with the agent
        result = writing_service.process_text(
            text,
            specific_tools=specific_tools if specific_tools else None,
            tone=tone if tone else None
        )

        # Save to database
        improvement = TextImprovement.objects.create(
            user=request.user if request.user.is_authenticated else None,
            original_text=text,
            improved_text=result['improved'],
            tools_used=[imp['tool'] for imp in result['improvements']],
            improvements_details=result['improvements'],
            analysis_results=result['analysis'],
            processing_time=result['processing_time']
        )

        # Update tool usage statistics
        for tool_name in improvement.tools_used:
            stats, created = ToolUsageStats.objects.get_or_create(
                tool_name=tool_name,
                defaults={'usage_count': 0}
            )
            stats.usage_count += 1
            stats.save()

        return JsonResponse({
            'success': True,
            'original': result['original'],
            'improved': result['improved'],
            'improvements': result['improvements'],
            'analysis': result['analysis'],
            'processing_time': result['processing_time'],
            'tools_used': improvement.tools_used,
            'improvement_id': improvement.id
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def analyze_text(request):
    """API endpoint to analyze text without making improvements."""
    try:
        text = request.POST.get('text', '').strip()

        if not text:
            return JsonResponse({'error': 'No text provided'}, status=400)

        # Get analysis results from LangGraph agent
        analysis_result = writing_service.agent.analyze_text(text)

        if analysis_result.get('success'):
            return JsonResponse({
                'success': True,
                'text': text,
                'analysis': analysis_result.get('analysis', {}),
                'recommended_tools': analysis_result.get('recommended_tools', []),
                'available_tools': writing_service.agent.get_available_tools()
            })
        else:
            return JsonResponse({
                'success': False,
                'text': text,
                'analysis': {},
                'recommended_tools': [],
                'available_tools': writing_service.agent.get_available_tools(),
                'error': analysis_result.get('error', 'Analysis failed')
            })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def history(request):
    """View to show user's improvement history."""
    if request.user.is_authenticated:
        improvements = TextImprovement.objects.filter(user=request.user)
    else:
        improvements = TextImprovement.objects.all()[:20]

    context = {
        'improvements': improvements,
    }
    return render(request, 'writing_assistant/history.html', context)


def stats(request):
    """View to show tool usage statistics."""
    tool_stats = ToolUsageStats.objects.all().order_by('-usage_count')
    total_improvements = TextImprovement.objects.count()

    context = {
        'tool_stats': tool_stats,
        'total_improvements': total_improvements,
    }
    return render(request, 'writing_assistant/stats.html', context)
