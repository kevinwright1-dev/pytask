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
      <div>
        <h1>Queue Status</h1>
        <p>Pending: {pending}</p>
        <p>Dead Letter: {deadLetter}</p>
      </div>
    )
}

function EnqueueForm( { onEnqueue } ) {
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
    <div>
      <h1>Enqueue Task</h1>
      <input
        type="text"
        placeholder="Function Name"
        value={fnName}
        onChange={(e) => setFnName(e.target.value)}
      />
      <input
        type="text"
        placeholder="Arguments (comma separated)"
        value={args}
        onChange={(e) => setArgs(e.target.value)}
      />
      <button onClick={handleSubmit}>Enqueue</button>
    </div>
  )
}
function ResultFeed({ taskIds }) {

  const [results, setResults] = useState([])

  useEffect(() => { 
    if (taskIds.length === 0) return () => {}
    const fetchResults = async () => {
      try {
        const responses = await Promise.all(taskIds.map(id => axios.get(`http://localhost:8000/task/${id}`)))
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
    <div>
      <h1>Task Results</h1>
      <ul>
        {results.map((result, index) => (
          <li key={index}>{JSON.stringify(result)}</li>
        ))}
      </ul>
    </div>
  )
}

export default function App() {
  const [taskIds, setTaskIds] = useState([])

  return (
    <div>
      <QueueStatus />
      <EnqueueForm onEnqueue={(id) => setTaskIds(prev => [...prev, id])} />
      <ResultFeed taskIds={taskIds} />
    </div>
  )
}

