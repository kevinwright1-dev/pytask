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
export default function App() {
  return <QueueStatus />
}