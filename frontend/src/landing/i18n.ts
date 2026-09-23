import { createContext, useContext } from 'react'

export type Lang = 'en' | 'ru' | 'kk'
export const LANGS: Lang[] = ['kk', 'ru', 'en']
export const LANG_CHIP: Record<Lang, string> = { kk: 'ҚАЗ', ru: 'РУС', en: 'ENG' }
export const LOCALE: Record<Lang, string> = { en: 'en-GB', ru: 'ru-RU', kk: 'kk-KZ' }

const en = {
  nav: { product: 'Product', how: 'How it works', hr: 'For HR', trust: 'Trust', docs: 'Docs', demo: 'Open a demo profile', talk: 'Talk to us', workspace: 'Open workspace', menu: 'Menu' },
  hero: {
    eyebrow: 'The AI decision layer for employee growth',
    title: 'Every employee deserves to know where they’re going.',
    sub: 'Career Quest turns scattered HR events into a clear, explainable path to the next grade — and shows HR where the catalog fails its people.',
    ctaDemo: 'Open a demo profile', ctaMethod: 'Read the method', live: 'Live', paused: 'Paused',
    myPath: 'My path', readiness: 'readiness for {grade}', current: 'Current', target: 'Target', goal: 'Goal',
    step: 'Step 1', monthsAt: '{n} months at the bank', hours: '{n} h', readinessAfter: 'Readiness after', expectedGain: 'Expected gain',
  },
  formats: { online: 'Online', offline: 'Offline', self_paced: 'Self-paced' } as Record<string, string>,
  types: { course: 'Course', workshop: 'Workshop', mentoring: 'Mentoring', certification: 'Certification', meetup: 'Meetup', compliance: 'Compliance', onboarding: 'Onboarding' } as Record<string, string>,
  proof: { builtFor: 'Built for Halyk Bank · HackAlem AI 2026', profiles: 'employee profiles', activities: 'development activities', skills: 'skills with grade requirements', traps: 'trap profiles handled', rules: 'rules decision', ai: 'AI explanation' },
  problem: {
    eyebrow: 'The problem', title: 'The bottleneck isn’t the training. It’s the decision.',
    c1t: 'A stream of notifications', c1b: 'Onboarding, courses, reviews, mentoring — they arrive as deadlines, not as a trajectory.',
    c2t: 'Formality by design', c2b: 'Completed on the due date, forgotten the day after. Nobody said what it was for.',
    c3t: 'Empty rooms', c3b: 'Voluntary events with no turnout — while the development budget is spent in full.',
    closing: 'Every one of these is a decision nobody explained.',
  },
  pipeline: {
    eyebrow: 'How it works', title: 'The decision layer',
    sub: 'Rules you can read, judgement where it helps, and a guard that never lets an invented number through.',
    s1t: 'Facts, not guesses', s1tag: 'Rules you can read', s1b: 'Effective skills with post-review completions applied and level caps respected. Target grade or career goal, weighted gaps, prerequisites, availability and the person’s own participation history.',
    s2t: 'AI decides — from a shortlist', s2tag: 'Judgement where it helps', s2b: 'The model chooses one to three of the engine’s top eight activities and explains them in the employee’s language. It can only cite factors that exist.',
    s3t: 'Validated, or it falls back', s3tag: 'Never a blank screen', s3b: 'Every answer is checked — ids from the shortlist, at least three real factors. One retry, then the rules result ships. No invented numbers.',
    engineers: 'For engineers', hide: 'Hide the formula',
    gap: 'the share of the weighted gap to the next grade that this activity closes — critical skills count three times',
    propensity: 'how the person responded to similar activities: completions versus refusals and no-shows',
    fit: 'how well the format suits them — completion rate per format, lower for offline when working remotely',
    availability: 'how soon they can start — self-paced or a session within 45 days scores highest',
    caption: 'Hover or focus a term — the matching factor lights up.', factors: 'Factors behind Step 1',
  },
  trap: {
    eyebrow: 'Why this, why not that', title: 'Single-factor rules fail on real people.',
    lowest: 'Lowest skill: {skill} ({level}) — declined {n} times.', critical: 'Critical gap: {skill} {have} → {need}.',
    naiveLabel: 'Recommend the lowest skill', questLabel: 'Career Quest', toggleNaive: 'Naive rule', toggleQuest: 'Career Quest',
    naiveNote: '{skill} activities declined ×{n}', naiveWhy: 'Aims at {skill} — the lowest number on the profile, and the one this person keeps turning down.',
    questWhy: '{skill} is the lowest skill, but it was declined {n} times. Career Quest closes the critical gap first and will suggest a lighter format later.',
    caption: 'We built {total} profiles designed to break single-factor rules. Career Quest handles {passed} of {total}.', link: 'See the evaluation',
  },
  progress: {
    eyebrow: 'Progress you can see', title: 'Finish something, and the map moves.',
    body: 'Mark an activity as completed: skills update, readiness for the next grade is recalculated, and the next recommendation takes its place.',
    button: 'Mark completed', done: 'Completed', readiness: 'Readiness for {grade}', nextUp: 'Next up', reset: 'Try again',
  },
  hr: {
    eyebrow: 'For HR', title: 'Where the catalog fails your people',
    sub: 'Organisation-level signals that turn into action: which competencies lag, who has no step to take, which activities people walk away from, and who may be quietly leaving.',
    lagging: 'Lagging competencies', below: '{n} below target', critical: 'critical ×{n}', noStep: 'No recommended step', people: '{n} people',
    participation: 'Participation by activity', dropOff: 'drop-off', attrition: 'Attrition risk', high: 'high', medium: 'medium',
    principle: 'No rankings. No leaderboards. Engagement data is never shown to other employees. Signals prompt a conversation — not a decision.',
    preview: 'Preview on synthetic data · initials only',
    reasons: { AT_TOP_NO_GOAL: 'Top grade, no goal', NO_ELIGIBLE_EVENTS: 'No matching activity', TARGET_REACHED: 'Target already met', PREREQUISITES_BLOCKED: 'Blocked by prerequisites', LOW_ENGAGEMENT: 'Low engagement' } as Record<string, string>,
  },
  principles: {
    eyebrow: 'Trust', title: 'Built on five principles',
    explainableT: 'Explainable', explainableB: 'Every number on screen has a source. Every empty result has a reason.',
    voluntaryT: 'Voluntary', voluntaryB: 'Invitations, not orders. “Not now” is a real answer that the system respects.',
    privateT: 'Private', privateB: 'An internal loop with separate employee and HR permissions. No one sees anyone else’s engagement.',
    sovereignT: 'Sovereign', sovereignB: 'Works with any OpenAI-compatible endpoint, or with none at all. One container, inside your perimeter.',
    multilingualT: 'Multilingual', multilingualB: 'Kazakh, Russian and English — for the interface and for every explanation.',
  },
  multi: { eyebrow: 'Қазақша · Русский · English', title: 'The same reasoning, in the employee’s language.', body: 'Explanations are written in the language the employee prefers — and switch instantly.' },
  arch: {
    eyebrow: 'Architecture', title: 'One container. Readable parts.', caption: 'FastAPI · React · a pure-Python rules engine · an optional AI layer · docker compose up',
    spa: 'React SPA', spaSub: 'employee · HR', api: 'FastAPI', apiSub: 'routing · roles', store: 'Store', storeSub: 'data · import · runtime',
    engine: 'Rules engine', engineSub: 'skills · gaps · eligibility · score', ai: 'AI layer', aiSub: 'decide · explain · validate',
    llm: 'OpenAI-compatible API', llmSub: 'optional · swappable', shortlist: 'top-8 shortlist', fallback: 'fallback',
  },
  roadmap: {
    eyebrow: 'What’s next', title: 'Where it goes from here', tag: 'Planned',
    r1t: 'Nudges in chat and calendar', r1b: 'Timely, voluntary invitations where people already work.',
    r2t: 'HR event builder', r2b: 'Turn a lagging competency into a new activity in two clicks.',
    r3t: 'Grade-transition simulation', r3b: '“If I complete these three, where am I?” — answered before you commit.',
    r4t: 'Mentoring matches', r4b: 'Pair people who need a skill with people who have it, using the same engine.',
  },
  final: {
    title: 'See your path.', sub: 'Open a real profile from the dataset. No sign-up, no password.',
    open: 'Open profile', search: 'or search any of the {n} profiles', searchPlaceholder: 'Name, role or ID', hr: 'Open the HR view',
    tags: { case_example: 'The case’s own example', speaking_trap: 'The public-speaking trap', cross_role: 'A goal in another role' } as Record<string, string>,
  },
  footer: { team: 'Team DevSpark', repo: 'Repository', event: 'HackAlem AI 2026 · Halyk Bank track', synthetic: 'All data is synthetic.', language: 'Language' },
  contact: {
    title: 'Let’s talk', close: 'Close', repo: 'Open the repository',
    body: 'Career Quest was built by team DevSpark at HackAlem AI 2026 for the Halyk Bank track. Interested in a pilot? The repository has everything needed to run it inside your perimeter.',
  },
}

export type Dict = typeof en

const ru: Dict = {
  nav: { product: 'Продукт', how: 'Как это работает', hr: 'Для HR', trust: 'Доверие', docs: 'Документация', demo: 'Открыть демо-профиль', talk: 'Связаться', workspace: 'Открыть кабинет', menu: 'Меню' },
  hero: {
    eyebrow: 'AI-слой решений для развития сотрудников',
    title: 'Каждый сотрудник заслуживает понимать, куда он движется.',
    sub: 'Career Quest превращает разрозненные HR-события в понятный и объяснимый путь к следующему грейду — и показывает HR, где каталог не помогает людям.',
    ctaDemo: 'Открыть демо-профиль', ctaMethod: 'Как это устроено', live: 'Вживую', paused: 'Пауза',
    myPath: 'Мой путь', readiness: 'готовность к {grade}', current: 'Сейчас', target: 'Цель', goal: 'Цель',
    step: 'Шаг 1', monthsAt: '{n} мес. в банке', hours: '{n} ч', readinessAfter: 'Готовность после', expectedGain: 'Ожидаемый рост',
  },
  formats: { online: 'Онлайн', offline: 'Офлайн', self_paced: 'В своём темпе' },
  types: { course: 'Курс', workshop: 'Воркшоп', mentoring: 'Менторство', certification: 'Сертификация', meetup: 'Митап', compliance: 'Комплаенс', onboarding: 'Онбординг' },
  proof: { builtFor: 'Сделано для Halyk Bank · HackAlem AI 2026', profiles: 'профилей сотрудников', activities: 'активностей развития', skills: 'навыков с требованиями по грейдам', traps: 'профилей-ловушек пройдено', rules: 'решение правил', ai: 'объяснение AI' },
  problem: {
    eyebrow: 'Проблема', title: 'Узкое место — не обучение. А решение.',
    c1t: 'Поток уведомлений', c1b: 'Онбординг, курсы, аттестации, менторство — всё приходит как дедлайны, а не как траектория.',
    c2t: 'Формальность по умолчанию', c2b: 'Пройдено в день дедлайна, забыто на следующий. Никто не объяснил, зачем.',
    c3t: 'Пустые залы', c3b: 'На добровольные активности никто не приходит — при том что бюджет на развитие расходуется полностью.',
    closing: 'За каждым из этого стоит решение, которое никто не объяснил.',
  },
  pipeline: {
    eyebrow: 'Как это работает', title: 'Слой решений',
    sub: 'Правила, которые можно прочитать, суждение там, где оно помогает, и проверка, которая не пропустит выдуманных чисел.',
    s1t: 'Факты, а не догадки', s1tag: 'Правила, которые можно прочитать', s1b: 'Эффективные навыки с учётом активностей после аттестации и потолков уровней. Целевой грейд или карьерная цель, взвешенные разрывы, предусловия, доступность и собственная история участия человека.',
    s2t: 'AI решает — из шорт-листа', s2tag: 'Суждение там, где оно помогает', s2b: 'Модель выбирает от одной до трёх из восьми лучших активностей движка и объясняет выбор на языке сотрудника. Ссылаться можно только на существующие факторы.',
    s3t: 'Проверено — или fallback', s3tag: 'Никогда не пустой экран', s3b: 'Каждый ответ проверяется: id из шорт-листа, минимум три реальных фактора. Одна повторная попытка — затем уходит результат правил. Никаких выдуманных чисел.',
    engineers: 'Для инженеров', hide: 'Скрыть формулу',
    gap: 'доля взвешенного разрыва до следующего грейда, которую закрывает активность; критические навыки считаются трижды',
    propensity: 'как человек реагировал на похожие активности: завершения против отказов и неявок',
    fit: 'насколько подходит формат: доля завершения по формату, ниже для офлайна при удалённой работе',
    availability: 'как скоро можно начать: в своём темпе или сессия в течение 45 дней — выше всего',
    caption: 'Наведите курсор или фокус на член формулы — подсветится соответствующий фактор.', factors: 'Факторы шага 1',
  },
  trap: {
    eyebrow: 'Почему это, а не то', title: 'Однофакторные правила ошибаются на реальных людях.',
    lowest: 'Самый слабый навык: {skill} ({level}) — отказов: {n}.', critical: 'Критический разрыв: {skill} {have} → {need}.',
    naiveLabel: 'Рекомендовать самый слабый навык', questLabel: 'Career Quest', toggleNaive: 'Наивное правило', toggleQuest: 'Career Quest',
    naiveNote: '{skill}: отказов ×{n}', naiveWhy: 'Нацелено на {skill} — самое низкое число в профиле и то, от чего человек раз за разом отказывается.',
    questWhy: '{skill} — самый слабый навык, но отказов по нему уже: {n}. Career Quest сначала закрывает критический разрыв, а более мягкий формат предложит позже.',
    caption: 'Мы собрали {total} профилей, которые ломают однофакторные правила. Career Quest проходит {passed} из {total}.', link: 'Смотреть оценку',
  },
  progress: {
    eyebrow: 'Прогресс, который видно', title: 'Завершите что-то — и карта сдвинется.',
    body: 'Отметьте активность выполненной: навыки обновятся, готовность к следующему грейду пересчитается, и на её место встанет следующая рекомендация.',
    button: 'Отметить выполненным', done: 'Выполнено', readiness: 'Готовность к {grade}', nextUp: 'Дальше', reset: 'Ещё раз',
  },
  hr: {
    eyebrow: 'Для HR', title: 'Где каталог не помогает людям',
    sub: 'Сигналы уровня организации, которые превращаются в действия: какие компетенции проседают, у кого нет следующего шага, с каких активностей уходят и кто может тихо уйти из компании.',
    lagging: 'Проседающие компетенции', below: '{n} ниже цели', critical: 'критично ×{n}', noStep: 'Нет рекомендованного шага', people: '{n} чел.',
    participation: 'Участие по активностям', dropOff: 'отток', attrition: 'Риск ухода', high: 'высокий', medium: 'средний',
    principle: 'Никаких рейтингов. Никаких лидербордов. Данные о вовлечённости не видны другим сотрудникам. Сигналы — повод для разговора, а не для решения.',
    preview: 'Превью на синтетических данных · только инициалы',
    reasons: { AT_TOP_NO_GOAL: 'Верхний грейд, нет цели', NO_ELIGIBLE_EVENTS: 'Нет подходящей активности', TARGET_REACHED: 'Цель уже достигнута', PREREQUISITES_BLOCKED: 'Мешают предусловия', LOW_ENGAGEMENT: 'Низкая вовлечённость' },
  },
  principles: {
    eyebrow: 'Доверие', title: 'Пять принципов',
    explainableT: 'Объяснимость', explainableB: 'У каждого числа на экране есть источник. У каждого пустого результата — причина.',
    voluntaryT: 'Добровольность', voluntaryB: 'Приглашения, а не приказы. «Не сейчас» — настоящий ответ, который система уважает.',
    privateT: 'Приватность', privateB: 'Внутренний контур с раздельными правами сотрудника и HR. Никто не видит вовлечённость других.',
    sovereignT: 'Суверенность', sovereignB: 'Работает с любым OpenAI-совместимым эндпоинтом — или вообще без него. Один контейнер внутри вашего периметра.',
    multilingualT: 'Многоязычность', multilingualB: 'Казахский, русский и английский — в интерфейсе и в каждом объяснении.',
  },
  multi: { eyebrow: 'Қазақша · Русский · English', title: 'То же рассуждение — на языке сотрудника.', body: 'Объяснения пишутся на языке, который выбрал сотрудник, и переключаются мгновенно.' },
  arch: {
    eyebrow: 'Архитектура', title: 'Один контейнер. Понятные части.', caption: 'FastAPI · React · движок правил на чистом Python · опциональный AI-слой · docker compose up',
    spa: 'React SPA', spaSub: 'сотрудник · HR', api: 'FastAPI', apiSub: 'маршруты · роли', store: 'Хранилище', storeSub: 'данные · импорт · runtime',
    engine: 'Движок правил', engineSub: 'навыки · разрывы · допуск · оценка', ai: 'AI-слой', aiSub: 'выбор · объяснение · проверка',
    llm: 'OpenAI-совместимый API', llmSub: 'опционально · заменяемо', shortlist: 'шорт-лист топ-8', fallback: 'fallback',
  },
  roadmap: {
    eyebrow: 'Что дальше', title: 'Куда это движется', tag: 'В планах',
    r1t: 'Подсказки в чате и календаре', r1b: 'Своевременные добровольные приглашения там, где люди уже работают.',
    r2t: 'Конструктор мероприятий для HR', r2b: 'Превратите проседающую компетенцию в новую активность за два клика.',
    r3t: 'Моделирование перехода на грейд', r3b: '«Если пройду эти три — где я окажусь?» — ответ до того, как вы решите.',
    r4t: 'Подбор менторов', r4b: 'Соединяйте тех, кому нужен навык, с теми, у кого он есть, — тем же движком.',
  },
  final: {
    title: 'Увидьте свой путь.', sub: 'Откройте реальный профиль из набора данных. Без регистрации и пароля.',
    open: 'Открыть профиль', search: 'или найдите любой из {n} профилей', searchPlaceholder: 'Имя, роль или ID', hr: 'Открыть HR-обзор',
    tags: { case_example: 'Пример из самого кейса', speaking_trap: 'Ловушка публичных выступлений', cross_role: 'Цель в другой роли' },
  },
  footer: { team: 'Команда DevSpark', repo: 'Репозиторий', event: 'HackAlem AI 2026 · трек Halyk Bank', synthetic: 'Все данные синтетические.', language: 'Язык' },
  contact: {
    title: 'Давайте поговорим', close: 'Закрыть', repo: 'Открыть репозиторий',
    body: 'Career Quest создан командой DevSpark на HackAlem AI 2026 для трека Halyk Bank. Интересен пилот? В репозитории есть всё, чтобы запустить его внутри вашего периметра.',
  },
}

const kk: Dict = {
  nav: { product: 'Өнім', how: 'Қалай жұмыс істейді', hr: 'HR үшін', trust: 'Сенім', docs: 'Құжаттама', demo: 'Демо-профильді ашу', talk: 'Байланысу', workspace: 'Кабинетті ашу', menu: 'Мәзір' },
  hero: {
    eyebrow: 'Қызметкерлерді дамытуға арналған AI шешім қабаты',
    title: 'Әр қызметкер қайда бара жатқанын білуге лайық.',
    sub: 'Career Quest шашыраңқы HR-оқиғаларды келесі грейдке апаратын түсінікті әрі негізделген жолға айналдырады — және HR-ға каталогтың адамдарға қай жерде көмектеспейтінін көрсетеді.',
    ctaDemo: 'Демо-профильді ашу', ctaMethod: 'Әдістеме', live: 'Тікелей', paused: 'Кідіріс',
    myPath: 'Менің жолым', readiness: '{grade} деңгейіне дайындық', current: 'Қазір', target: 'Мақсат', goal: 'Мақсат',
    step: '1-қадам', monthsAt: 'Банкте {n} ай', hours: '{n} сағ', readinessAfter: 'Кейінгі дайындық', expectedGain: 'Күтілетін өсім',
  },
  formats: { online: 'Онлайн', offline: 'Офлайн', self_paced: 'Өз қарқынымен' },
  types: { course: 'Курс', workshop: 'Воркшоп', mentoring: 'Тәлімгерлік', certification: 'Сертификаттау', meetup: 'Митап', compliance: 'Комплаенс', onboarding: 'Онбординг' },
  proof: { builtFor: 'Halyk Bank үшін жасалған · HackAlem AI 2026', profiles: 'қызметкер профилі', activities: 'даму белсенділігі', skills: 'грейд талаптары бар дағды', traps: 'тұзақ-профиль өтілді', rules: 'ережелер шешімі', ai: 'AI түсіндірмесі' },
  problem: {
    eyebrow: 'Мәселе', title: 'Кедергі — оқуда емес. Шешімде.',
    c1t: 'Хабарламалар ағыны', c1b: 'Онбординг, курстар, аттестация, тәлімгерлік — бәрі траектория емес, дедлайн ретінде келеді.',
    c2t: 'Әдепкі формальдылық', c2b: 'Дедлайн күні өтеді, келесі күні ұмытылады. Не үшін екенін ешкім түсіндірмеді.',
    c3t: 'Бос залдар', c3b: 'Ерікті іс-шараларға ешкім келмейді — ал даму бюджеті толық жұмсалады.',
    closing: 'Мұның әрқайсысының артында ешкім түсіндірмеген шешім тұр.',
  },
  pipeline: {
    eyebrow: 'Қалай жұмыс істейді', title: 'Шешім қабаты',
    sub: 'Оқуға болатын ережелер, пайдалы жерде пайымдау және ойдан шығарылған санды өткізбейтін тексеріс.',
    s1t: 'Болжам емес, фактілер', s1tag: 'Оқуға болатын ережелер', s1b: 'Аттестациядан кейінгі аяқталған белсенділіктер ескерілген, деңгей шектері сақталған тиімді дағдылар. Мақсатты грейд немесе мансаптық мақсат, салмақталған алшақтықтар, алғышарттар, қолжетімділік және адамның өз қатысу тарихы.',
    s2t: 'AI шешеді — қысқа тізімнен', s2tag: 'Пайымдау қажет жерде', s2b: 'Модель қозғалтқыштың үздік сегіз белсенділігінің бірден үшке дейінгісін таңдап, оны қызметкердің тілінде түсіндіреді. Тек бар факторларға ғана сілтеме жасай алады.',
    s3t: 'Тексерілді — немесе fallback', s3tag: 'Бос экран ешқашан болмайды', s3b: 'Әр жауап тексеріледі: id қысқа тізімнен, кемінде үш нақты фактор. Бір рет қайталау — одан кейін ережелер нәтижесі беріледі. Ойдан шығарылған сандар жоқ.',
    engineers: 'Инженерлерге', hide: 'Формуланы жасыру',
    gap: 'келесі грейдке дейінгі салмақталған алшақтықтың осы белсенділік жабатын үлесі; маңызды дағдылар үш есе есептеледі',
    propensity: 'адам ұқсас белсенділіктерге қалай жауап берді: аяқтаулар мен бас тартулар, келмей қалулар',
    fit: 'формат қаншалықты сәйкес: формат бойынша аяқтау үлесі, қашықтан жұмыс істегенде офлайн үшін төменірек',
    availability: 'қаншалықты тез бастауға болады: өз қарқынымен немесе 45 күн ішіндегі сессия ең жоғары бағаланады',
    caption: 'Формула мүшесіне меңзерді немесе фокусты апарыңыз — сәйкес фактор жарықтанады.', factors: '1-қадамның факторлары',
  },
  trap: {
    eyebrow: 'Неге бұл, неге анау емес', title: 'Бір факторлы ережелер нақты адамдарда қателеседі.',
    lowest: 'Ең әлсіз дағды: {skill} ({level}) — бас тартулар: {n}.', critical: 'Маңызды алшақтық: {skill} {have} → {need}.',
    naiveLabel: 'Ең әлсіз дағдыны ұсыну', questLabel: 'Career Quest', toggleNaive: 'Қарапайым ереже', toggleQuest: 'Career Quest',
    naiveNote: '{skill}: бас тарту ×{n}', naiveWhy: '{skill} дағдысына бағытталған — профильдегі ең төмен сан және адам үнемі бас тартатын нәрсе.',
    questWhy: '{skill} — ең әлсіз дағды, бірақ одан {n} рет бас тартылған. Career Quest алдымен маңызды алшақтықты жабады, ал жеңілірек форматты кейін ұсынады.',
    caption: 'Бір факторлы ережелерді бұзуға арналған {total} профиль жасадық. Career Quest {total} профильдің {passed}-ін өтеді.', link: 'Бағалауды көру',
  },
  progress: {
    eyebrow: 'Көрінетін прогресс', title: 'Бірдеңені аяқтаңыз — карта жылжиды.',
    body: 'Белсенділікті аяқталды деп белгілеңіз: дағдылар жаңарады, келесі грейдке дайындық қайта есептеледі, ал оның орнына келесі ұсыныс келеді.',
    button: 'Аяқталды деп белгілеу', done: 'Аяқталды', readiness: '{grade} деңгейіне дайындық', nextUp: 'Келесі', reset: 'Қайта көру',
  },
  hr: {
    eyebrow: 'HR үшін', title: 'Каталог адамдарға қай жерде көмектеспейді',
    sub: 'Әрекетке айналатын ұйым деңгейіндегі сигналдар: қай құзыреттер артта қалады, кімде келесі қадам жоқ, адамдар қай белсенділіктерден кетеді және кім үнсіз кетуі мүмкін.',
    lagging: 'Артта қалған құзыреттер', below: '{n} мақсаттан төмен', critical: 'маңызды ×{n}', noStep: 'Ұсынылған қадам жоқ', people: '{n} адам',
    participation: 'Белсенділіктер бойынша қатысу', dropOff: 'кету', attrition: 'Кету қаупі', high: 'жоғары', medium: 'орташа',
    principle: 'Рейтинг жоқ. Лидерборд жоқ. Қатысу деректері басқа қызметкерлерге көрсетілмейді. Сигналдар — шешім емес, әңгімеге себеп.',
    preview: 'Синтетикалық деректердегі алдын ала қарау · тек инициалдар',
    reasons: { AT_TOP_NO_GOAL: 'Жоғарғы грейд, мақсат жоқ', NO_ELIGIBLE_EVENTS: 'Сәйкес белсенділік жоқ', TARGET_REACHED: 'Мақсатқа жеткен', PREREQUISITES_BLOCKED: 'Алғышарттар кедергі', LOW_ENGAGEMENT: 'Төмен қатысу' },
  },
  principles: {
    eyebrow: 'Сенім', title: 'Бес қағида',
    explainableT: 'Түсіндірмелілік', explainableB: 'Экрандағы әр санның көзі бар. Әр бос нәтиженің себебі бар.',
    voluntaryT: 'Еріктілік', voluntaryB: 'Бұйрық емес, шақыру. «Қазір емес» — жүйе құрметтейтін нақты жауап.',
    privateT: 'Құпиялылық', privateB: 'Қызметкер мен HR құқықтары бөлінген ішкі контур. Ешкім басқалардың қатысуын көрмейді.',
    sovereignT: 'Егемендік', sovereignB: 'Кез келген OpenAI-үйлесімді эндпоинтпен немесе мүлде онсыз жұмыс істейді. Сіздің периметріңіздің ішіндегі бір контейнер.',
    multilingualT: 'Көптілділік', multilingualB: 'Қазақ, орыс және ағылшын тілдері — интерфейсте де, әр түсіндірмеде де.',
  },
  multi: { eyebrow: 'Қазақша · Русский · English', title: 'Сол пайымдау — қызметкердің тілінде.', body: 'Түсіндірмелер қызметкер таңдаған тілде жазылады және бірден ауысады.' },
  arch: {
    eyebrow: 'Архитектура', title: 'Бір контейнер. Түсінікті бөліктер.', caption: 'FastAPI · React · таза Python-дағы ережелер қозғалтқышы · қосымша AI қабаты · docker compose up',
    spa: 'React SPA', spaSub: 'қызметкер · HR', api: 'FastAPI', apiSub: 'маршруттар · рөлдер', store: 'Қойма', storeSub: 'деректер · импорт · runtime',
    engine: 'Ережелер қозғалтқышы', engineSub: 'дағдылар · алшақтықтар · рұқсат · баға', ai: 'AI қабаты', aiSub: 'таңдау · түсіндіру · тексеру',
    llm: 'OpenAI-үйлесімді API', llmSub: 'міндетті емес · ауыстыруға болады', shortlist: 'топ-8 қысқа тізім', fallback: 'fallback',
  },
  roadmap: {
    eyebrow: 'Әрі қарай', title: 'Бұдан әрі қайда', tag: 'Жоспарда',
    r1t: 'Чат пен күнтізбедегі еске салулар', r1b: 'Адамдар жұмыс істейтін жерде уақтылы, ерікті шақырулар.',
    r2t: 'HR-ға арналған іс-шара құрастырушы', r2b: 'Артта қалған құзыретті екі шертумен жаңа белсенділікке айналдырыңыз.',
    r3t: 'Грейдке өтуді модельдеу', r3b: '«Осы үшеуін аяқтасам, қай жерде боламын?» — шешім қабылдамас бұрын жауап.',
    r4t: 'Тәлімгерлерді іріктеу', r4b: 'Дағды керек адамдарды сол дағдысы барлармен дәл сол қозғалтқыш арқылы байланыстырыңыз.',
  },
  final: {
    title: 'Өз жолыңызды көріңіз.', sub: 'Деректер жиынынан нақты профильді ашыңыз. Тіркелусіз, құпиясөзсіз.',
    open: 'Профильді ашу', search: 'немесе {n} профильдің кез келгенін іздеңіз', searchPlaceholder: 'Аты, рөлі немесе ID', hr: 'HR шолуын ашу',
    tags: { case_example: 'Кейстің өз мысалы', speaking_trap: 'Көпшілік алдында сөйлеу тұзағы', cross_role: 'Басқа рөлдегі мақсат' },
  },
  footer: { team: 'DevSpark командасы', repo: 'Репозиторий', event: 'HackAlem AI 2026 · Halyk Bank трегі', synthetic: 'Барлық деректер синтетикалық.', language: 'Тіл' },
  contact: {
    title: 'Сөйлесейік', close: 'Жабу', repo: 'Репозиторийді ашу',
    body: 'Career Quest-ті DevSpark командасы HackAlem AI 2026-да Halyk Bank трегі үшін жасады. Пилот қызықтыра ма? Репозиторийде оны сіздің периметріңіздің ішінде іске қосуға қажеттінің бәрі бар.',
  },
}

export const DICTS: Record<Lang, Dict> = { en, ru, kk }

export function fmt(template: string, vars: Record<string, string | number>) {
  return template.replace(/\{(\w+)\}/g, (_, key: string) => String(vars[key] ?? ''))
}

export function initialLang(): Lang {
  try { const saved = localStorage.getItem('cq-landing-lang'); if (saved === 'en' || saved === 'ru' || saved === 'kk') return saved } catch { /* storage unavailable */ }
  const browser = (typeof navigator !== 'undefined' ? navigator.language : 'en').toLowerCase()
  return browser.startsWith('kk') ? 'kk' : browser.startsWith('ru') ? 'ru' : 'en'
}

export const LangContext = createContext<{ lang: Lang; t: Dict; setLang: (lang: Lang) => void }>({ lang: 'en', t: en, setLang: () => undefined })
export const useLang = () => useContext(LangContext)
