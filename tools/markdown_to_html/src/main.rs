use std::env;
use std::fs;
use pulldown_cmark::{html, Options, Parser};

fn main() {
    let path = env::args().nth(1).unwrap_or_else(|| {
        eprintln!("Error: file path required");
        std::process::exit(1);
    });

    let markdown = fs::read_to_string(&path).unwrap_or_else(|e| {
        eprintln!("Error reading {}: {}", path, e);
        std::process::exit(1);
    });

    let mut opts = Options::empty();
    opts.insert(Options::ENABLE_TABLES);
    opts.insert(Options::ENABLE_STRIKETHROUGH);
    opts.insert(Options::ENABLE_TASKLISTS);

    let parser = Parser::new_ext(&markdown, opts);
    let mut output = String::new();
    html::push_html(&mut output, parser);
    print!("{}", output);
}
