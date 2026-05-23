import json
import os
from datetime import datetime

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from issues.models import Reporter, Issue, CriticalIssue, LowPriorityIssue

# ── file paths (sit next to manage.py) ──────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORTERS_FILE = os.path.join(BASE_DIR, "reporters.json")
ISSUES_FILE = os.path.join(BASE_DIR, "issues.json")


# ── helpers ──────────────────────────────────────────────────────────────────
def _read(path):
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        return json.load(f)


def _write(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def _reporter_exists(reporter_id):
    return any(r["id"] == reporter_id for r in _read(REPORTERS_FILE))


# ── reporter views ────────────────────────────────────────────────────────────
@csrf_exempt
@require_http_methods(["GET", "POST"])
def reporters(request):
    if request.method == "POST":
        return _create_reporter(request)
    return _get_reporters(request)


def _create_reporter(request):
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "Invalid JSON body"}, status=400)

    try:
        rep = Reporter(
            id=data["id"],
            name=data.get("name", ""),
            email=data.get("email", ""),
            team=data.get("team", ""),
        )
        rep.validate()
    except (KeyError, TypeError):
        return JsonResponse({"error": "Missing required field: id"}, status=400)
    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=400)

    all_reporters = _read(REPORTERS_FILE)
    if any(r["id"] == rep.id for r in all_reporters):
        return JsonResponse({"error": f"Reporter with id {rep.id} already exists"}, status=400)

    all_reporters.append(rep.to_dict())
    _write(REPORTERS_FILE, all_reporters)
    return JsonResponse(rep.to_dict(), status=201)


def _get_reporters(request):
    all_reporters = _read(REPORTERS_FILE)
    reporter_id = request.GET.get("id")

    if reporter_id is not None:
        try:
            reporter_id = int(reporter_id)
        except ValueError:
            return JsonResponse({"error": "id must be an integer"}, status=400)
        for r in all_reporters:
            if r["id"] == reporter_id:
                return JsonResponse(r, status=200)
        return JsonResponse({"error": "Reporter not found"}, status=404)

    return JsonResponse(all_reporters, safe=False, status=200)


# ── issue views ───────────────────────────────────────────────────────────────
@csrf_exempt
@require_http_methods(["GET", "POST"])
def issues(request):
    if request.method == "POST":
        return _create_issue(request)
    return _get_issues(request)


def _create_issue(request):
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "Invalid JSON body"}, status=400)

    priority = data.get("priority", "")

    try:
        kwargs = dict(
            id=data["id"],
            title=data.get("title", ""),
            description=data.get("description", ""),
            status=data.get("status", ""),
            priority=priority,
            reporter_id=data.get("reporter_id"),
            created_at=str(datetime.now()),
        )
    except KeyError:
        return JsonResponse({"error": "Missing required field: id"}, status=400)

    # instantiate the right subclass
    if priority == "critical":
        issue = CriticalIssue(**kwargs)
    elif priority == "low":
        issue = LowPriorityIssue(**kwargs)
    else:
        issue = Issue(**kwargs)

    try:
        issue.validate()
    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=400)

    # check reporter exists
    if not _reporter_exists(issue.reporter_id):
        return JsonResponse({"error": f"Reporter with id {issue.reporter_id} not found"}, status=404)

    all_issues = _read(ISSUES_FILE)
    if any(i["id"] == issue.id for i in all_issues):
        return JsonResponse({"error": f"Issue with id {issue.id} already exists"}, status=400)

    all_issues.append(issue.to_dict())
    _write(ISSUES_FILE, all_issues)

    response_data = issue.to_dict()
    response_data["message"] = issue.describe()
    return JsonResponse(response_data, status=201)


def _get_issues(request):
    all_issues = _read(ISSUES_FILE)
    issue_id = request.GET.get("id")
    status_filter = request.GET.get("status")

    if issue_id is not None:
        try:
            issue_id = int(issue_id)
        except ValueError:
            return JsonResponse({"error": "id must be an integer"}, status=400)
        for i in all_issues:
            if i["id"] == issue_id:
                return JsonResponse(i, status=200)
        return JsonResponse({"error": "Issue not found"}, status=404)

    if status_filter is not None:
        filtered = [i for i in all_issues if i["status"] == status_filter]
        return JsonResponse(filtered, safe=False, status=200)

    return JsonResponse(all_issues, safe=False, status=200)
