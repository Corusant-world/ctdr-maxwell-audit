# Infinite Context Challenge (public‑safe) — “Reaper Effect” без токсичности

**Цель:** создать инженерный шум и forcing‑function для NVIDIA owner’ов через независимую валидацию.  
**Критерий успеха:** 1) появляется инженерный owner/слот, 2) запускается NDA‑оценка, 3) приоритет зафиксирован публично (arXiv).

---

## 0) Правила безопасности (жёстко)

- Никаких DPX kernel source / PTX / SASS / bindings.
- Никаких “перпетуум мобиле”, “реверсивность” как физическое утверждение, и прочих непроверяемых заявлений.
- Только public‑safe: **метрики + воспроизводимость + чёткий NDA‑план**.
- Никаких угроз, оскорблений, “я уничтожу индустрию”. Вместо этого: *“я открываю независимую валидацию и запускаю evaluation window”*.

---

## 0.5) Тезис “Reality OS” (инженерно‑корректная версия, public‑safe)

Нельзя писать “вечный двигатель” / “отключаем память” — это физически неверно и выглядит как шарлатанство.

Формулировка, которая **дерзкая**, но инженерно‑корректная:

- **H100 is not a calculator — it’s a high‑bandwidth simulator of structure.**
- **My approach shifts the workload away from N^2 materialization and excessive memory movement into an indexed, locality‑aware retrieval regime — reducing bytes moved and therefore J/query.**

---

## 1) What is the challenge (1 sentence)

**Challenge:** показать, что “бесконечный контекст” — это не токены, а **детерминированное retrieval‑ядро** без N x N материализации, и что это можно делать на H100 с реальными метриками энергии.

---

## 2) Public‑safe claims (то, что можно говорить публично)

### Claim A — OOM wall (hard feasibility boundary)
Любая система, которая **должна** материализовать N x N fp16 similarity/attention, упирается в физический потолок HBM и становится невозможной при больших N.

### Claim B — Indexed retrieval avoids N^2
Есть путь, где memory‑рост ~ O(N) и retrieval обходится без матрицы N^2.

### Claim C — Energy per useful query (what CFO cares about)
Если ты уменьшаешь **байты движения памяти** и **объём сканирования**, можно уменьшать J/query на порядки (не “ближе к Ландауэру”, а “дешевле дата‑центру”).

---

## 2.3) “Energy Audit” (public‑safe, no Landauer / no NFT)

Цель: сделать энергию **контрактным языком**, а не маркетингом.

**Определения (жёстко):**

- **Verified Query (VQ)** = запрос, для которого есть измеримая корректность (например `truth_mode=unique_match` → `top1_correct`).
- **J/VQ** = `energy_j / top1_correct` (если accuracy < 1.0, это наказывает “быстро, но в молоко”).
- **Receipts** = NVML samples (power/util/temp) + интеграция Joules + параметры прогона (duration, n_candidates, etc).

**Запрещено (публично):**

- Утверждения про “10^7–10^9 раз выше предела Ландауэра”.
- “Я приближаюсь к Ландауэру”.
- “Heat Signature NFT / blockchain”.

**Разрешено (и лучше):**

- “Я публикую **криптографический receipt hash**: sha256(artifact.json), чтобы артефакт нельзя было подменить незаметно.”
- “Я показываю измеримые бюджеты: power/thermal/util + J/VQ — это дешево проверить и дорого подделать.”

---

## 2.4) Что я имею в виду под “harness + artifacts”

Это не “идея”. Это **воспроизводимый runner**, который:

- принимает `seed` + параметры (N, workload),
- генерит датасет процедурно (без скачивания “10M документов”),
- гоняет baseline и Omega‑path,
- пишет **артефакты** (JSON/логи/receipts) так, чтобы любой мог проверить.

Минимальный набор артефактов (пример):

- `scenario.json` (seed + параметры)
- `dataset_spec.json` (как строится датасет)
- `truth.json` (ground truth для exactness)
- `results.json` (accuracy + latency stats + QPS)
- `receipt_energy.json` (опционально: NVML/nvidia-smi receipts)
- `receipt_hashes.json` (sha256 всех артефактов)

Готовый public-safe runner (процедурная “Библиотека Вавилона”):

- `public_teaser/babel_challenge/run_babel_challenge.py`

---

## 3) The “Reaper Effect” (engineering‑correct wording)

**Reaper Effect** = не “я убиваю рынок”, а:

- “На конкретном классе задач (exact structured retrieval / exact match / hierarchy‑aware retrieval) типовой embedding‑ANN pipeline деградирует: либо цена растёт, либо качество падает.”
- “Я показываю режим, где deterministic retrieval держит качество и масштаб.”

Если кто-то хочет спорить — отлично: спор превращается в **benchmark**, а не в мнение.

---

## 4) Minimal public deliverables (что реально успеть до Dec 31)

**D0 (сразу, когда готово):**
- arXiv preprint (public priority)
- 1 страница “Challenge rules + how to reproduce baseline OOM wall”
- 2 графика: (1) memory scaling N^2 vs O(N), (2) J/query vs метод (public‑safe)
- 60–90 секундный клип: `nvidia-smi` + запуск бенча + итоговый JSON (без кода ядра)

Runbook: `public_teaser/FORCING_PACKAGE_RUNBOOK.md`.

**D1 (по желанию):**
- GitHub issue/discussion в нужном репо (routing ask) + ссылка на arXiv/тизер

---

## 5) Distribution (non‑spam)

Это делается как **один синхронный удар**, а не “много маленьких”.

Один пост в 1–2 местах максимум (не “везде и сразу”):
- Hacker News (если есть арXiv + 2 графика)
- r/MachineLearning или r/LocalLLaMA (один пост)
- NVIDIA Developer Forums (только как routing reply, см. `forum_post_routing_template.md`)

---

## 6) The ask (what I want)

**20–30 min technical screen → NDA → 14‑day remote pilot**.  
Под NDA: контейнер/runbook + evidence bundle; без repo handover.


