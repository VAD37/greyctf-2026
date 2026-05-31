const mineflayer = require('mineflayer')
const net = require('net')
const Vec3 = require('vec3').Vec3

const bot = mineflayer.createBot({
  host: '127.0.0.1', port: 25565, username: 'ctfbot', version: '1.21.11', auth: 'offline'
})

let ready = false
bot.on('error', e => console.log('ERR', e.message))
bot.on('kicked', r => console.log('KICKED', r))
bot.once('spawn', () => { console.log('SPAWNED'); setTimeout(()=>{ ready=true; console.log('READY') }, 1500) })

function reply(sock, msg){ try{ sock.write(msg+'\n') }catch(e){} }

const server = net.createServer(sock => {
  let buf=''
  sock.on('data', async d => {
    buf+=d.toString()
    let idx
    while((idx=buf.indexOf('\n'))>=0){
      const line=buf.slice(0,idx).trim(); buf=buf.slice(idx+1)
      if(!line) continue
      const parts=line.split(/\s+/)
      const cmd=parts[0]
      try{
        if(cmd==='ping'){ reply(sock, ready?'pong':'notready') }
        else if(cmd==='click'){
          // click lever at x y z  (parts[1..3])
          const x=+parts[1], y=+parts[2], z=+parts[3]
          // tp via chat command (bot must be op+creative)
          bot.chat(`/tp @s ${x+1} ${y+1} ${z} 90 0`)
          await bot.waitForTicks(4)
          const blk=bot.blockAt(new Vec3(x,y,z))
          if(!blk){ reply(sock,'ERR noblock'); continue }
          await bot.lookAt(new Vec3(x+0.5,y+0.5,z+0.5), true)
          await bot.activateBlock(blk)
          await bot.waitForTicks(2)
          const b2=bot.blockAt(new Vec3(x,y,z))
          const powered = b2 && b2.getProperties && b2.getProperties().powered
          reply(sock, `ok name=${blk.name} powered=${powered}`)
        }
        else if(cmd==='blk'){
          const x=+parts[1],y=+parts[2],z=+parts[3]
          const b=bot.blockAt(new Vec3(x,y,z))
          reply(sock, b? `${b.name} ${JSON.stringify(b.getProperties?b.getProperties():{})}`:'null')
        }
        else reply(sock,'ERR unknown')
      }catch(e){ reply(sock,'ERR '+e.message) }
    }
  })
})
server.listen(4000, '127.0.0.1', ()=>console.log('CTRL listening 4000'))
