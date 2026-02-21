import argparse
import re
import sys
from collections import Counter
from typing import Optional

def word_count(text: str) -> int:
    return len(text.split())

def char_count(text: str, include_spaces: bool = True) -> int:
    if include_spaces:
        return len(text)
    return len(text.replace(' ', ''))

def summarize_text(text: str, max_sentences: int = 3) -> str:
    if not text or not text.strip():
        return ''
    all_words = re.findall(r'\w+', text.lower())
    word_freq = Counter(all_words)
    sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
    def score(sent: str) -> float:
        words = re.findall(r'\w+', sent.lower())
        return sum(word_freq.get(w, 0) for w in words)
    sorted_sents = sorted(sentences, key=score, reverse=True)
    top = sorted_sents[:max_sentences]
    return '. '.join(top) + '.'

def handle_command(message: str) -> Optional[str]:
    try:
        parts = message.strip().split()
        if not parts or parts[0] != 'text_utility':
            return None
        if len(parts) < 2:
            return 'Usage: text_utility <word_count|char_count|summarize> [options] <text>'
        subcmd = parts[1]
        if subcmd == 'word_count':
            if len(parts) < 3:
                return 'Usage: text_utility word_count <text>'
            text = ' '.join(parts[2:])
            count = word_count(text)
            return f'Word count: {count}'
        elif subcmd == 'char_count':
            include_spaces = True
            start = 2
            if len(parts) > 2 and parts[2] == 'no_spaces':
                include_spaces = False
                start = 3
            if len(parts) <= start:
                return 'Usage: text_utility char_count [no_spaces] <text>'
            text = ' '.join(parts[start:])
            count = char_count(text, include_spaces)
            spaces_str = '' if include_spaces else ' (no spaces)'
            return f'Character count{spaces_str}: {count}'
        elif subcmd == 'summarize':
            max_s = 3
            start = 2
            if len(parts) > 2 and parts[2].isdigit():
                max_s = int(parts[2])
                start = 3
            if len(parts) <= start:
                return 'Usage: text_utility summarize [max_sentences] <text>'
            text = ' '.join(parts[start:])
            summary = summarize_text(text, max_s)
            return f'Summary ({max_s} sentences):\n{summary}'
        else:
            return f'Unknown subcommand: {subcmd}. Available: word_count, char_count, summarize'
    except Exception as e:
        return f'Error processing command: {str(e)}'

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Text Utility CLI')
    subparsers = parser.add_subparsers(dest='subcmd', required=True)
    wc_parser = subparsers.add_parser('word_count')
    wc_parser.add_argument('text', nargs='+')
    cc_parser = subparsers.add_parser('char_count')
    cc_parser.add_argument('text', nargs='+')
    cc_parser.add_argument('--no-spaces', dest='include_spaces', action='store_false')
    cc_parser.set_defaults(include_spaces=True)
    sum_parser = subparsers.add_parser('summarize')
    sum_parser.add_argument('text', nargs='+')
    sum_parser.add_argument('--max-sentences', type=int, default=3)
    args = parser.parse_args()
    text = ' '.join(args.text)
    try:
        if args.subcmd == 'word_count':
            print(word_count(text))
        elif args.subcmd == 'char_count':
            print(char_count(text, args.include_spaces))
        elif args.subcmd == 'summarize':
            print(summarize_text(text, args.max_sentences))
    except Exception as e:
        print(f'Error: {e}', file=sys.stderr)