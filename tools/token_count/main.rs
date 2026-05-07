use std::env;
use std::fs;

fn main() {
    let path = env::args().nth(1).unwrap_or_else(|| {
        eprintln!("Error: file path required");
        std::process::exit(1);
    });

    let text = fs::read_to_string(&path).unwrap_or_else(|e| {
        eprintln!("Error reading {}: {}", path, e);
        std::process::exit(1);
    });

    if text.trim().is_empty() {
        eprintln!("Error: file is empty");
        std::process::exit(1);
    }

    let chars = text.chars().count();
    let words = text.split_whitespace().count();
    // rough GPT-style estimate: ~4 chars per token
    let estimated_tokens = (chars as f64 / 4.0).ceil() as usize;

    println!(
        "{{\n  \"chars\": {},\n  \"words\": {},\n  \"estimated_tokens\": {}\n}}",
        chars, words, estimated_tokens
    );
}
