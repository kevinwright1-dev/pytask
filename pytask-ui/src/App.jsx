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

      const interval = setInterval(fetchQueueStatus, 5000)
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

function EnqueueForm() {
  const [fnName, setFnName] = useState('')
  const [args, setArgs] = useState('')
  const handleSubmit = async () => {
  const parsedArgs = args.split(',').map(arg => arg.trim())
  await axios.post('http://localhost:8000/task/enqueue', {
    fn: fnName,
    args: parsedArgs,
    kwargs: {}
  })
  // clear the form
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


export default function App() {
  return (
    <div>
      <QueueStatus />
      <EnqueueForm />
    </div>
  )
}

