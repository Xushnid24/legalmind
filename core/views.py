import json
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import Case
from .ai_utils import analyze_case_structured, search_similar_cases, generate_document


# ---------- CRUD дела ----------

def case_list(request):
    cases = Case.objects.all().order_by("-id")
    copied_cases = []
    return render(request, "core/case_list.html", {
        "cases": cases,
        "copied_cases": copied_cases
    })


def case_detail(request, pk):
    case = get_object_or_404(Case, pk=pk)
    return render(request, "core/case_detail.html", {"case": case})


def case_create(request):
    if request.method == "POST":
        title = request.POST.get("title")
        text = request.POST.get("text")

        if title and text:
            Case.objects.create(title=title, text=text)

        return redirect("case_list")

    return render(request, "core/case_create.html")


def case_delete(request, pk):
    case = get_object_or_404(Case, pk=pk)
    case.delete()
    return redirect("case_list")


# ---------- ИИ-инструменты ----------

def analyze_case_view(request):
    result = None

    if request.method == "POST":
        case_text = request.POST.get("case_text", "").strip()

        if case_text:
            if "history_analyze" not in request.session:
                request.session["history_analyze"] = []

            history = request.session["history_analyze"]
            history.append(("user", case_text))

            result = analyze_case_structured(case_text, history)

            history.append(("assistant", json.dumps(result, ensure_ascii=False)))
            request.session["history_analyze"] = history
            request.session.modified = True

    return render(request, "core/analyze_case.html", {"result": result})


@csrf_exempt
def search_cases_view(request):
    if "history_search" not in request.session:
        request.session["history_search"] = []

    if request.method == "POST":
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"reply": []}, status=400)

        user_message = data.get("message", "").strip()

        if not user_message:
            return JsonResponse({"reply": []})

        history = request.session["history_search"]
        history.append(("user", user_message))

        results = search_similar_cases(user_message, history)

        history.append(("assistant", json.dumps(results, ensure_ascii=False)))
        request.session["history_search"] = history
        request.session.modified = True

        return JsonResponse({"reply": results})

    return render(request, "core/search_cases.html")


def generate_document_view(request):
    if "history_docs" not in request.session:
        request.session["history_docs"] = []

    generated_text = None

    if request.method == "POST":
        user_message = request.POST.get("message", "").strip()

        if user_message:
            history = request.session["history_docs"]

            history.append(("user", user_message))
            generated_text = generate_document(user_message, history)
            history.append(("assistant", generated_text))

            request.session["history_docs"] = history
            request.session.modified = True

    return render(request, "core/generate_document.html", {"generated_text": generated_text})