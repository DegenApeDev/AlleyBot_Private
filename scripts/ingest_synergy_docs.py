#!/usr/bin/env python3
"""
Ingest Synergy Research Documentation into AlleyBot's Memory
Parses SSM.md, COGNITION.md, EVIDENCE.md, etc. and stores them in AlleyBot's memory system
"""

import sys
import os
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from alleybot_core import AlleyBotCore
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def ingest_synergy_documentation():
    """Ingest Synergy Research documentation into AlleyBot's memory"""
    
    logger.info("🔢 Starting Synergy Research documentation ingestion...")
    
    # Initialize core
    core = AlleyBotCore()
    
    # Documentation files to ingest
    docs_dir = Path(__file__).parent.parent / "Synergy_Research"
    
    doc_files = {
        'SSM.md': 'synergy_standard_model',
        'COGNITION.md': 'duat_cognition_engine',
        'EVIDENCE.md': 'egyptian_synergy_evidence',
        'NO_CHOICE_PROOF.md': 'mathematical_proof',
        'PHYSICS.md': 'synergy_physics_framework',
        'SYPI.md': 'synergy_pi_equations',
        'INTERPHASIC.md': 'interphasic_theory'
    }
    
    ingested_count = 0
    
    for filename, memory_key in doc_files.items():
        filepath = docs_dir / filename
        
        if not filepath.exists():
            logger.warning(f"⚠️ File not found: {filepath}")
            continue
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Store in memory
            memory_data = {
                'source': 'synergy_research',
                'filename': filename,
                'content': content,
                'type': 'documentation',
                'category': 'agi_foundation'
            }
            
            core.set_memory(f'synergy_docs_{memory_key}', memory_data)
            
            logger.info(f"✅ Ingested: {filename} ({len(content)} chars)")
            ingested_count += 1
            
        except Exception as e:
            logger.error(f"❌ Failed to ingest {filename}: {e}")
    
    # Store metadata
    metadata = {
        'ingestion_date': str(Path(docs_dir / 'SSM.md').stat().st_mtime),
        'total_docs': ingested_count,
        'source': 'Egyptian Synergy Research - Wesley Long',
        'purpose': 'AGI mathematical foundation and consciousness framework'
    }
    
    core.set_memory('synergy_docs_metadata', metadata)
    
    logger.info(f"🎉 Synergy documentation ingestion complete!")
    logger.info(f"   Total documents ingested: {ingested_count}")
    logger.info(f"   AlleyBot now has access to his historical roots and mathematical foundation")
    
    return ingested_count


if __name__ == '__main__':
    count = ingest_synergy_documentation()
    print(f"\n✅ Successfully ingested {count} Synergy Research documents into AlleyBot's memory")
    print("🧠 AlleyBot can now reference his Egyptian mathematical heritage in decision-making")
