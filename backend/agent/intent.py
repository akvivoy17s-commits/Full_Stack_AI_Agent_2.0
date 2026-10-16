"""Single source of truth for prompt intent (used by Autopilot and the planner so both pick the same layout)."""
import re

APP_PROMPT = re.compile(
    r"\b(to-?dos?|task (manager|management|list)|notes?( app)?|note[- ]taking|trackers?|planner|scheduler|record manager|crud|admin panel|"
    r"management (system|app|tool|software)|\w+ management|\bcrm\b|erp|hrms|inventory|bookings?( system| app)?|appointments?|student portal|"
    r"attendance|expense|budget( app)?|dashboard|content management|cms|kanban|invoic(e|ing)|calculator( app)?)\b", re.I)
MARKETING_PROMPT = re.compile(
    r"\b(landing page|marketing (web)?site|company website|personal website|coming soon|"
    r"(?<!investment )(?<!stock )(?<!crypto )portfolio (website|site|page)|^\s*(a |my )?portfolio\b|"
    r"\b(personal|my|online|creative|professional|designer|developer|photographer|artist|photography) portfolio\b)", re.I)
SPECIALIST_PROMPT = re.compile(r"\b(e-?commerce|online store|marketplace|shopping cart|checkout|chat app|messaging platform|social network|streaming platform|ai chatbot|chatbot)\b", re.I)


def is_app_prompt(text: str, allow_dashboard: bool = True) -> bool:
    """True for data-management app prompts (todo, CRM, booking...), False for marketing sites and specialist builds.
    allow_dashboard=False ignores the bare word "dashboard" (e.g. "a dashboard widget" on a landing page)."""
    probe = text if allow_dashboard else re.sub(r"\bdashboard\b", " ", text, flags=re.I)
    return bool(APP_PROMPT.search(probe)) and not MARKETING_PROMPT.search(text) and not SPECIALIST_PROMPT.search(text)
