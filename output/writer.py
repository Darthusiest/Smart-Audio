import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from utils.logger import get_logger
from config import OUTPUT_DIR, OUTPUT_SETTINGS

logger = get_logger("output_writer")

class OutputWriter:
    """Handles saving results to various output formats"""
    
    def __init__(self):
        self.output_dir = OUTPUT_DIR
        self.settings = OUTPUT_SETTINGS
    
    def save_summary(self, original_text: str, summary: str, translated_summary: str,
                    target_language: str, audio_path: Optional[Path] = None,
                    output_format: str = "txt") -> Path:
        """Save summary and translation to file"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if output_format == "txt":
            return self._save_as_txt(original_text, summary, translated_summary, 
                                   target_language, audio_path, timestamp)
        elif output_format == "pdf":
            return self._save_as_pdf(original_text, summary, translated_summary, 
                                   target_language, audio_path, timestamp)
        elif output_format == "json":
            return self._save_as_json(original_text, summary, translated_summary, 
                                    target_language, audio_path, timestamp)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")
    
    def _save_as_txt(self, original_text: str, summary: str, translated_summary: str,
                     target_language: str, audio_path: Optional[Path], timestamp: str) -> Path:
        """Save results as text file"""
        
        filename = f"summary_{timestamp}.txt"
        output_path = self.output_dir / filename
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("=== AUDIO SUMMARY & TRANSLATION ===\n\n")
                
                if audio_path:
                    f.write(f"Source Audio: {audio_path.name}\n")
                
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Target Language: {target_language}\n\n")
                
                f.write("=" * 50 + "\n")
                f.write("ORIGINAL TRANSCRIPT\n")
                f.write("=" * 50 + "\n")
                f.write(original_text)
                f.write("\n\n")
                
                f.write("=" * 50 + "\n")
                f.write("SUMMARY\n")
                f.write("=" * 50 + "\n")
                f.write(summary)
                f.write("\n\n")
                
                f.write("=" * 50 + "\n")
                f.write(f"TRANSLATED SUMMARY ({target_language.upper()})\n")
                f.write("=" * 50 + "\n")
                f.write(translated_summary)
                f.write("\n")
            
            logger.info(f"Results saved to: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to save text file: {e}")
            raise
    
    def _save_as_pdf(self, original_text: str, summary: str, translated_summary: str,
                     target_language: str, audio_path: Optional[Path], timestamp: str) -> Path:
        """Save results as PDF file"""
        
        filename = f"summary_{timestamp}.pdf"
        output_path = self.output_dir / filename
        
        try:
            doc = SimpleDocTemplate(str(output_path), pagesize=letter)
            story = []
            
            # Get styles
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=16,
                spaceAfter=20
            )
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=14,
                spaceAfter=12
            )
            body_style = styles['Normal']
            
            # Title
            story.append(Paragraph("Audio Summary & Translation", title_style))
            story.append(Spacer(1, 12))
            
            # Metadata
            if audio_path:
                story.append(Paragraph(f"<b>Source Audio:</b> {audio_path.name}", body_style))
            story.append(Paragraph(f"<b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", body_style))
            story.append(Paragraph(f"<b>Target Language:</b> {target_language}", body_style))
            story.append(Spacer(1, 20))
            
            # Original transcript
            story.append(Paragraph("Original Transcript", heading_style))
            story.append(Paragraph(original_text, body_style))
            story.append(Spacer(1, 20))
            
            # Summary
            story.append(Paragraph("Summary", heading_style))
            story.append(Paragraph(summary, body_style))
            story.append(Spacer(1, 20))
            
            # Translated summary
            story.append(Paragraph(f"Translated Summary ({target_language.upper()})", heading_style))
            story.append(Paragraph(translated_summary, body_style))
            
            # Build PDF
            doc.build(story)
            
            logger.info(f"Results saved to: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to save PDF file: {e}")
            raise
    
    def _save_as_json(self, original_text: str, summary: str, translated_summary: str,
                      target_language: str, audio_path: Optional[Path], timestamp: str) -> Path:
        """Save results as JSON file"""
        
        filename = f"summary_{timestamp}.json"
        output_path = self.output_dir / filename
        
        try:
            data = {
                "metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "target_language": target_language,
                    "source_audio": str(audio_path) if audio_path else None,
                    "original_text_length": len(original_text),
                    "summary_length": len(summary),
                    "translated_summary_length": len(translated_summary)
                },
                "content": {
                    "original_text": original_text,
                    "summary": summary,
                    "translated_summary": translated_summary
                }
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Results saved to: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to save JSON file: {e}")
            raise
    
    