import React from 'react'
import { createRoot } from 'react-dom/client'
import './app.css'

type InputItem = { id: number; title: string; problem: string; hypothesis?: string | null; impact_score: number; tags: string[]; owner?: string | null; status: string; created_at: number }
type ExperimentItem = { id: number; input_id: number; objective: string; owner?: string | null; status: string; created_at: number }

const App = () => {
    const [health, setHealth] = React.useState<string>('checking...')
    const [title, setTitle] = React.useState('')
    const [problem, setProblem] = React.useState('')
    const [hypothesis, setHypothesis] = React.useState('')
    const [impact, setImpact] = React.useState(5)
    const [inputs, setInputs] = React.useState<InputItem[]>([])
    const [experiments, setExperiments] = React.useState<ExperimentItem[]>([])
    const [objective, setObjective] = React.useState('')
    const [tags, setTags] = React.useState('')
    const [owner, setOwner] = React.useState('')
    const [assignOwners, setAssignOwners] = React.useState<Record<number, string>>({})
    const [filter, setFilter] = React.useState({ owner: '', tag: '', status: '' })
    React.useEffect(() => {
        fetch('/api/health').then(r => r.json()).then(j => setHealth(j.status)).catch(() => setHealth('down'))
        refresh()
    }, [])
    const refresh = () => {
        const q = new URLSearchParams()
        if (filter.owner.trim()) q.set('owner', filter.owner.trim())
        if (filter.tag.trim()) q.set('tag', filter.tag.trim())
        if (filter.status.trim()) q.set('status', filter.status.trim())
        fetch('/api/bridge/inputs' + (q.toString() ? `?${q.toString()}` : '')).then(r => r.json()).then(setInputs).catch(() => setInputs([]))
        fetch('/api/bridge/experiments').then(r => r.json()).then(setExperiments).catch(() => setExperiments([]))
    }
    const submit = async (e: React.FormEvent) => {
        e.preventDefault()
        const tagsArr = tags.split(',').map(t => t.trim()).filter(Boolean)
        await fetch('/api/bridge/inputs', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ title, problem, hypothesis, impact_score: impact, tags: tagsArr, owner: owner || undefined }) })
        setTitle(''); setProblem(''); setHypothesis(''); setImpact(5); setTags(''); setOwner('')
        refresh()
    }
    const approve = async (inputId: number) => {
        if (!objective.trim()) return
        await fetch(`/api/bridge/experiments/${inputId}?objective=${encodeURIComponent(objective)}`, { method: 'POST' })
        setObjective(''); refresh()
    }
    return (
        <div className="app">
            <h1>Full‑Stack Ecosystem</h1>
            <p>API health: {health}</p>

            <h2 className="bridge-title">Research Bridge</h2>
            <form onSubmit={submit} className="bridge-form">
                <input placeholder="Title" value={title} onChange={e => setTitle(e.target.value)} required />
                <textarea placeholder="Problem" value={problem} onChange={e => setProblem(e.target.value)} required />
                <input placeholder="Hypothesis (optional)" value={hypothesis} onChange={e => setHypothesis(e.target.value)} />
                <input placeholder="Tags (comma-separated)" value={tags} onChange={e => setTags(e.target.value)} />
                <input placeholder="Owner (optional)" value={owner} onChange={e => setOwner(e.target.value)} />
                <label>Impact score: {impact}
                    <input type="range" min={1} max={10} value={impact} onChange={e => setImpact(parseInt(e.target.value))} />
                </label>
                <button type="submit">Submit research input</button>
            </form>

            <div className="bridge-filters">
                <input placeholder="Filter owner" value={filter.owner} onChange={e => setFilter({ ...filter, owner: e.target.value })} />
                <input placeholder="Filter tag" value={filter.tag} onChange={e => setFilter({ ...filter, tag: e.target.value })} />
                <select aria-label="Filter by status" value={filter.status} onChange={e => setFilter({ ...filter, status: e.target.value })}>
                    <option value="">Any status</option>
                    <option value="new">new</option>
                    <option value="reviewing">reviewing</option>
                    <option value="approved">approved</option>
                    <option value="rejected">rejected</option>
                </select>
                <button onClick={refresh}>Apply</button>
            </div>

            <div className="bridge-grid">
                <div>
                    <h3>Inputs</h3>
                    <ul>
                        {inputs.map(i => (
                            <li key={i.id}>
                                <strong>{i.title}</strong> — impact {i.impact_score} — status {i.status} {i.owner ? `— owner ${i.owner}` : ''}
                                <div className="bridge-problem">{i.problem}</div>
                                {i.tags?.length ? <div className="bridge-tags">tags: {i.tags.join(', ')}</div> : null}
                                <div className="bridge-actions">
                                    <input placeholder="Objective" value={objective} onChange={e => setObjective(e.target.value)} />
                                    <button onClick={() => approve(i.id)}>Approve → Experiment</button>
                                </div>
                                <div className="bridge-actions">
                                    <input placeholder="Set owner" value={assignOwners[i.id] ?? ''} onChange={e => setAssignOwners(prev => ({ ...prev, [i.id]: e.target.value }))} />
                                    <button onClick={async () => { const newOwner = assignOwners[i.id]; if (!newOwner) return; await fetch(`/api/bridge/inputs/${i.id}/owner`, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ owner: newOwner }) }); setAssignOwners(prev => ({ ...prev, [i.id]: '' })); refresh() }}>Assign</button>
                                    <select aria-label={`Update status for ${i.title}`} onChange={async e => { await fetch(`/api/bridge/inputs/${i.id}/status`, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ status: e.target.value }) }); refresh() }} defaultValue={i.status}>
                                        <option value="new">new</option>
                                        <option value="reviewing">reviewing</option>
                                        <option value="approved">approved</option>
                                        <option value="rejected">rejected</option>
                                    </select>
                                </div>
                            </li>
                        ))}
                    </ul>
                </div>
                <div>
                    <h3>Experiments</h3>
                    <ul>
                        {experiments.map(e => (
                            <li key={e.id}>
                                <strong>#{e.id}</strong> from input {e.input_id} — {e.objective} ({e.status})
                            </li>
                        ))}
                    </ul>
                </div>
            </div>
        </div>
    )
}

const root = createRoot(document.getElementById('root')!)
root.render(<App />)
