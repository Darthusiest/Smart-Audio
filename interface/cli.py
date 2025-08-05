import click
from pathlib import Path
from typing import Optional
from utils.logger import get_logger

logger = get_logger("cli")

@click.command()
@click.option('--audio', '-a', 'audio_path', type=click.Path(exists=True), 
              help='Path to audio file')
@click.option('--language', '-l', 'target_language', default='en',
              help='Target language for translation (default: en)')
@click.option('--output-format', '-f', 'output_format', 
              type=click.Choice(['txt', 'pdf', 'json']), default='txt',
              help='Output format (default: txt)')
@click.option('--summary-style', '-s', 'summary_style',
              type=click.Choice(['concise', 'detailed', 'bullet', 'academic']), 
              default='concise',
              help='Summary style (default: concise)')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def main(audio_path: Optional[str], target_language: str, output_format: str, 
         summary_style: str, verbose: bool):
    """Smart Audio Summarizer & Translator
    
    Process audio files to extract, summarize, and translate content.
    """
    
    if verbose:
        logger.info("Verbose mode enabled")
    
    if not audio_path:
        # Interactive mode
        audio_path = prompt_user_input("Enter path to audio file: ")
        target_language = prompt_user_input("Enter target language (e.g., en, es, fr): ", default="en")
        output_format = prompt_user_input("Enter output format (txt/pdf/json): ", default="txt")
        summary_style = prompt_user_input("Enter summary style (concise/detailed/bullet/academic): ", default="concise")
    
    # Validate inputs
    audio_file = Path(audio_path)
    if not audio_file.exists():
        click.echo(f"Error: Audio file not found: {audio_path}")
        return
    
    # Process the audio
    try:
        from app import process_audio_file
        result = process_audio_file(
            audio_path=audio_file,
            target_language=target_language,
            output_format=output_format,
            summary_style=summary_style
        )
        
        click.echo(f"\n Processing completed!")
        click.echo(f"📄 Output saved to: {result}")
        
    except Exception as e:
        click.echo(f" Error processing audio: {e}")
        if verbose:
            logger.exception("Processing failed")

def prompt_user_input(prompt: str, default: str = "") -> str:
    """Prompt user for input with optional default value"""
    
    if default:
        user_input = input(f"{prompt} [{default}]: ").strip()
        return user_input if user_input else default
    else:
        return input(f"{prompt}: ").strip()

@click.command()
@click.option('--list-languages', is_flag=True, help='List supported languages')
@click.option('--test-audio', type=click.Path(exists=True), help='Test with sample audio file')
def info(list_languages: bool, test_audio: Optional[str]):
    """Show information about the application"""
    
    if list_languages:
        from translation.translator import Translator
        translator = Translator()
        languages = translator.get_supported_languages()
        
        click.echo("Supported languages:")
        for code, name in languages.items():
            click.echo(f"  {code}: {name}")
    
    elif test_audio:
        click.echo(f"Testing with audio file: {test_audio}")
        # Add test functionality here
    
    else:
        click.echo("Smart Audio Summarizer & Translator")
        click.echo("Version: 1.0.0")
        click.echo("\nUsage:")
        click.echo("  python -m interface.cli --audio file.mp3 --language es")
        click.echo("  python -m interface.cli --help")

if __name__ == '__main__':
    main() 