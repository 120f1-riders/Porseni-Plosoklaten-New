/**
 * Custom Node server for cPanel (Passenger) / VPS deployment.
 * Passenger launches this file (set as "Application startup file").
 * Locally on Emergent we still use "next dev" via supervisor — this file
 * is only used in production hosting (cPanel / PM2 / VPS).
 */
const { createServer } = require('http')
const next = require('next')

const port = process.env.PORT || 3000
const app = next({ dev: false })
const handle = app.getRequestHandler()

app.prepare().then(() => {
  createServer((req, res) => handle(req, res)).listen(port, () => {
    console.log('SIM Porseni running on port ' + port)
  })
}).catch((err) => {
  console.error('Failed to start Next.js server:', err)
  process.exit(1)
})
