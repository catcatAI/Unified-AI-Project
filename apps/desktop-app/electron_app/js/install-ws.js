const https = require('https')
const fs = require('fs')
const path = require('path')
const zlib = require('zlib')

const wsDir = path.join(__dirname, 'node_modules', 'ws')
const tmpFile = path.join(process.env.TEMP || '/tmp', 'ws.tgz')

if (!fs.existsSync(wsDir)) {
  fs.mkdirSync(wsDir, { recursive: true })
}

console.log('Downloading ws package...')
const file = fs.createWriteStream(tmpFile)
https.get('https://registry.npmjs.org/ws/-/ws-8.18.3.tgz', (res) => {
  res.pipe(file)
  file.on('finish', () => {
    file.close()
    console.log('Downloaded, extracting...')
    extractTgz(tmpFile, wsDir)
  })
}).on('error', (err) => {
  console.error('Download failed:', err)
})

function extractTgz(tgzPath, destDir) {
  const fileData = fs.readFileSync(tgzPath)
  const buffer = Buffer.from(fileData)

  // Simple tar extraction for a single-file package
  // npm tgz has files starting with "package/" prefix
  const str = buffer.toString('latin1')
  const startMarker = 'package/'
  const packageIndex = str.indexOf(startMarker)

  if (packageIndex === -1) {
    console.error('Invalid package format')
    return
  }

  // Find all files in the tar
  const files = {}
  let pos = packageIndex

  while (pos < buffer.length - 512) {
    // Read tar header (512 bytes)
    const header = buffer.slice(pos, pos + 512)
    if (header[0] === 0) break // Null block = end of archive

    const name = header.slice(0, 100).toString('utf8').replace(/\0/g, '')
    const sizeStr = header.slice(124, 136).toString('utf8').replace(/\0/g, '')
    const size = parseInt(sizeStr, 8)

    pos += 512

    if (name.startsWith('package/') && size > 0) {
      const content = buffer.slice(pos, pos + size)
      const fileName = name.slice(8) // Remove "package/" prefix
      const filePath = path.join(destDir, fileName)

      const dir = path.dirname(filePath)
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true })
      }

      fs.writeFileSync(filePath, content)
      console.log('Extracted:', fileName)
    }

    pos += size
    if (size % 512 !== 0) {
      pos += 512 - (size % 512)
    }
  }

  console.log('Done! Files in ws dir:', fs.readdirSync(wsDir))
}