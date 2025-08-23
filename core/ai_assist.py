from config import settings
import openai

if settings.openai_api_key:
    openai.api_key = settings.openai_api_key
else:
    openai = None

async def summarize_market(top_routes: list[dict]) -> str:
    if not settings.openai_api_key or not settings.openai_ranking_enabled:
        lines = []
        for r in top_routes[:5]:
            lines.append(f"المسار: {[x[0] for x in r.get('route', [])]} | صافي={r.get('net_pct',0):.4f}% | طول={r.get('length',0)}")
        return "\n".join(lines)

    prompt = "لخص فرص المراجحة الحالية والمخاطر باختصار بالعربية:\n" + "\n".join([
        f"{i+1}. {[x[0] for x in r.get('route', [])]} net={r.get('net_pct',0):.4f}% len={r.get('length',0)}" for i,r in enumerate(top_routes[:20])
    ])

    try:
        resp = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role":"user","content":prompt}],
            max_tokens=300
        )
        return resp['choices'][0]['message']['content']
    except Exception as e:
        return f"OpenAI error: {e}"
