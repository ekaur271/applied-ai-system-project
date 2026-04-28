# Frontend Basics

## Overview
The frontend is everything the user sees and interacts with. For most web projects, this means HTML, CSS, and JavaScript. Modern projects often use a framework like React, Vue, or Svelte. Start simple and add a framework when the complexity justifies it.

## When to Use a Framework
**Use plain HTML/CSS/JS when:**
- The project is mostly static content
- There is minimal user interaction
- You are building a prototype or MVP quickly

**Use React/Vue/Svelte when:**
- The UI has complex, dynamic state
- Multiple components need to share and sync data
- You are building a single-page application (SPA)

## Component Structure (React)
Break the UI into small, reusable components. Each component does one thing.

```
App
├── NavBar
├── ProjectList
│   └── ProjectCard (repeated)
├── ProjectDetail
│   ├── PlanDisplay
│   └── StepList
└── Footer
```

```jsx
function ProjectCard({ project }) {
    return (
        <div className="card">
            <h2>{project.name}</h2>
            <p>{project.description}</p>
        </div>
    );
}
```

## State Management
State is data that changes over time and affects what the UI displays.

**Local state** — belongs to one component:
```jsx
const [query, setQuery] = useState("");
const [loading, setLoading] = useState(false);
```

**Shared state** — needed by multiple components. Lift state up to the nearest common parent, or use a state manager (Zustand, Redux) for large apps.

## Making API Calls from the Frontend
Use `fetch` or `axios` to call your backend:

```javascript
async function fetchPlan(projectGoal) {
    try {
        const response = await fetch("/api/plan", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${token}`
            },
            body: JSON.stringify({ goal: projectGoal })
        });

        if (!response.ok) {
            throw new Error(`HTTP error: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error("Failed to fetch plan:", error);
        throw error;
    }
}
```

Always handle loading states and errors in the UI — never leave the user staring at a blank screen.

## Handling Loading and Error States
```jsx
function PlanDisplay({ goal }) {
    const [plan, setPlan] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    async function handleSubmit() {
        setLoading(true);
        setError(null);
        try {
            const result = await fetchPlan(goal);
            setPlan(result);
        } catch (e) {
            setError("Failed to generate plan. Please try again.");
        } finally {
            setLoading(false);
        }
    }

    if (loading) return <p>Generating your plan...</p>;
    if (error) return <p className="error">{error}</p>;
    if (!plan) return null;
    return <PlanOutput plan={plan} />;
}
```

## Forms and Input Handling
```jsx
function GoalForm({ onSubmit }) {
    const [goal, setGoal] = useState("");

    function handleSubmit(e) {
        e.preventDefault();
        if (!goal.trim()) return;
        onSubmit(goal);
    }

    return (
        <form onSubmit={handleSubmit}>
            <textarea
                value={goal}
                onChange={(e) => setGoal(e.target.value)}
                placeholder="Describe your project idea..."
                maxLength={500}
            />
            <button type="submit" disabled={!goal.trim()}>
                Generate Plan
            </button>
        </form>
    );
}
```

## CSS Organization
- Use CSS modules or a utility framework (Tailwind) to avoid style conflicts
- Keep component styles next to the component file
- Use semantic class names that describe what something is, not how it looks

## Common Frontend Mistakes
- No loading states — users see nothing and think the app is broken
- No error handling — silent failures confuse users
- Storing tokens in localStorage (use httpOnly cookies for security-sensitive tokens)
- Making API calls directly from deeply nested components instead of lifting them up
- Not handling edge cases: empty lists, very long text, slow network
