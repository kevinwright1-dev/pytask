import { useState, useEffect } from 'react'
import axios from 'axios'

function QueueStatus() {
  const [pending, setPending] = useState(0)
  const [deadLetter, setDeadLetter] = useState(0)

  useEffect(() => {
    const fetchQueueStatus = async () => {
      try {
        const response = await axios.get('http://localhost:8000/queue/status')
        setPending(response.data.pending)
        setDeadLetter(response.data.dead_letter)
      } catch (error) {
        console.error('Error fetching queue status:', error)
      }
    }
    fetchQueueStatus()
    const interval = setInterval(fetchQueueStatus, 1000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="grid grid-cols-2 gap-4 mb-6">
      <div className="bg-zinc-800 rounded-xl p-6 border border-zinc-700">
        <p className="text-zinc-400 text-sm uppercase tracking-widest mb-1">Pending</p>
        <p className="text-4xl font-bold text-white">{pending}</p>
      </div>
      <div className="bg-zinc-800 rounded-xl p-6 border border-zinc-700">
        <p className="text-zinc-400 text-sm uppercase tracking-widest mb-1">Dead Letter</p>
        <p className="text-4xl font-bold text-red-400">{deadLetter}</p>
      </div>
    </div>
  )
}
function EnqueueForm({ onEnqueue }) {
  const [fnName, setFnName] = useState('')
  const [args, setArgs] = useState('')

  const handleSubmit = async () => {
    const parsedArgs = args.split(',').map(arg => arg.trim())
    const response = await axios.post('http://localhost:8000/task/enqueue', {
      fn: fnName,
      args: parsedArgs,
      kwargs: {}
    })
    onEnqueue(response.data.task_id)
    setFnName('')
    setArgs('')
  }

  return (
    <div className="bg-zinc-800 rounded-xl p-6 border border-zinc-700 mb-6">
      <h2 className="text-zinc-400 text-sm uppercase tracking-widest mb-4">Enqueue Task</h2>
      <div className="flex gap-3">
        <input
          type="text"
          placeholder="Function name e.g. add"
          value={fnName}
          onChange={(e) => setFnName(e.target.value)}
          className="flex-1 bg-zinc-900 text-white border border-zinc-600 rounded-lg px-4 py-2 text-sm focus:outline-none focus:border-blue-500"
        />
        <input
          type="text"
          placeholder="Args e.g. 6, 3"
          value={args}
          onChange={(e) => setArgs(e.target.value)}
          className="flex-1 bg-zinc-900 text-white border border-zinc-600 rounded-lg px-4 py-2 text-sm focus:outline-none focus:border-blue-500"
        />
        <button
          onClick={handleSubmit}
          className="bg-blue-600 hover:bg-blue-500 text-white px-6 py-2 rounded-lg text-sm font-medium transition-colors"
        >
          Enqueue
        </button>
      </div>
    </div>
  )
}

function ResultFeed({ taskIds }) {
  const [results, setResults] = useState([])

  useEffect(() => {
    if (taskIds.length === 0) return () => {}
    const fetchResults = async () => {
      try {
        const responses = await Promise.all(
          taskIds.map(id => axios.get(`http://localhost:8000/task/${id}`))
        )
        setResults(responses.map(res => res.data))
      } catch (error) {
        console.error('Error fetching results:', error)
      }
    }
    fetchResults()
    const interval = setInterval(fetchResults, 1000)
    return () => clearInterval(interval)
  }, [taskIds])

  return (
    <div className="bg-zinc-800 rounded-xl p-6 border border-zinc-700">
      <h2 className="text-zinc-400 text-sm uppercase tracking-widest mb-4">Task Results</h2>
      {results.length === 0 ? (
        <p className="text-zinc-500 text-sm">No tasks yet. Enqueue something above.</p>
      ) : (
        <table className="w-full text-sm">
          <thead>
            <tr className="text-zinc-400 text-left border-b border-zinc-700">
              <th className="pb-2 font-medium">Task ID</th>
              <th className="pb-2 font-medium">Status</th>
              <th className="pb-2 font-medium">Value</th>
            </tr>
          </thead>
          <tbody>
            {results.map((result, index) => (
              <tr key={index} className="border-b border-zinc-700 last:border-0">
                <td className="py-3 font-mono text-zinc-400 text-xs">{result.task_id}</td>
                <td className="py-3">
                  <span className={`px-2 py-1 rounded text-xs font-medium ${
                    result.result?.status === 'SUCCESS'
                      ? 'bg-green-900 text-green-300'
                      : result.result === null
                      ? 'bg-yellow-900 text-yellow-300'
                      : 'bg-red-900 text-red-300'
                  }`}>
                    {result.result?.status ?? 'PENDING'}
                  </span>
                </td>
                <td className="py-3 font-mono text-white text-xs">
                  {result.result?.value !== undefined
                    ? JSON.stringify(result.result.value)
                    : '...'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}

export default function App() {
  const [taskIds, setTaskIds] = useState([])

  return (
    <div className="min-h-screen bg-zinc-900 text-white p-8">
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-white">pytask</h1>
          <p className="text-zinc-400 text-sm mt-1">distributed task queue dashboard</p>
        </div>
        <QueueStatus />
        <EnqueueForm onEnqueue={(id) => setTaskIds(prev => [...prev, id])} />
        <ResultFeed taskIds={taskIds} />
      </div>
    </div>
  )
}