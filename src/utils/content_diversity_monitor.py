"""
Content Diversity Monitor for AlleyBot
Tracks post diversity and provides anti-repetition warnings
"""
import time
from typing import Dict, List, Optional
from collections import Counter
from datetime import datetime, timedelta


class ContentDiversityMonitor:
    """Monitor content diversity across platforms to prevent repetitive posting"""
    
    def __init__(self):
        self.diversity_thresholds = {
            'similarity_warning': 0.7,
            'similarity_block': 0.85,
            'theme_repetition_limit': 3,
            'time_window_hours': 24
        }
    
    def analyze_diversity(self, platform: str, recent_posts: List[str]) -> Dict:
        """Analyze content diversity and provide recommendations"""
        if not recent_posts:
            return {'status': 'no_data', 'recommendation': 'Start posting to build diversity baseline'}
        
        analysis = {
            'status': 'analyzed',
            'post_count': len(recent_posts),
            'diversity_score': 0.0,
            'issues': [],
            'recommendations': [],
            'themes': self._extract_themes(recent_posts),
            'similarities': []
        }
        
        # Theme analysis
        theme_counts = Counter(analysis['themes'])
        most_common_theme = theme_counts.most_common(1)[0] if theme_counts else None
        
        if most_common_theme and most_common_theme[1] >= self.diversity_thresholds['theme_repetition_limit']:
            analysis['issues'].append(f"Repetitive theme: '{most_common_theme[0]}' appears {most_common_theme[1]} times")
            analysis['recommendations'].append(f"Vary topics - reduce '{most_common_theme[0]}' content")
        
        # Similarity analysis (if we have sentence transformers available)
        try:
            similarities = self._calculate_similarities(recent_posts)
            analysis['similarities'] = similarities
            
            if similarities:
                avg_similarity = sum(similarities) / len(similarities)
                analysis['diversity_score'] = 1.0 - avg_similarity
                
                if avg_similarity >= self.diversity_thresholds['similarity_block']:
                    analysis['issues'].append(f"High similarity detected: {avg_similarity:.2f}")
                    analysis['recommendations'].append("Content too similar to recent posts - consider different angle")
                elif avg_similarity >= self.diversity_thresholds['similarity_warning']:
                    analysis['recommendations'].append("Moderate similarity - try more unique approach")
        except Exception as e:
            print(f"⚠️ Similarity analysis failed: {e}")
        
        # Generate overall status
        if analysis['issues']:
            analysis['status'] = 'warning' if len(analysis['issues']) == 1 else 'critical'
        else:
            analysis['status'] = 'good'
        
        return analysis
    
    def _extract_themes(self, posts: List[str]) -> List[str]:
        """Extract dominant themes from posts"""
        themes = []
        theme_keywords = {
            'ai': ['ai', 'agent', 'artificial', 'intelligence', 'autonomous'],
            'crypto': ['crypto', 'token', 'blockchain', 'defi', 'bitcoin', 'eth'],
            'development': ['code', 'build', 'develop', 'programming', 'tech'],
            'community': ['community', 'social', 'network', 'connect', 'engage'],
            'market': ['market', 'price', 'trading', 'investment', 'trend']
        }
        
        for post in posts:
            post_lower = post.lower()
            for theme, keywords in theme_keywords.items():
                if any(keyword in post_lower for keyword in keywords):
                    themes.append(theme)
                    break
        
        return themes
    
    def _calculate_similarities(self, posts: List[str]) -> List[float]:
        """Calculate pairwise similarities between posts"""
        try:
            from sentence_transformers import SentenceTransformer
            from sklearn.metrics.pairwise import cosine_similarity
            import numpy as np
            
            model = SentenceTransformer('all-MiniLM-L6-v2')
            embeddings = model.encode(posts)
            
            similarities = []
            for i in range(len(embeddings) - 1):
                sim = cosine_similarity([embeddings[i]], [embeddings[i + 1]])[0][0]
                similarities.append(sim)
            
            return similarities
        except ImportError:
            # Fallback to simple word overlap if sentence transformers not available
            return self._simple_similarity(posts)
    
    def _simple_similarity(self, posts: List[str]) -> List[float]:
        """Simple word overlap similarity as fallback"""
        similarities = []
        for i in range(len(posts) - 1):
            words1 = set(posts[i].lower().split())
            words2 = set(posts[i + 1].lower().split())
            
            if not words1 or not words2:
                similarities.append(0.0)
                continue
            
            intersection = words1.intersection(words2)
            union = words1.union(words2)
            
            similarity = len(intersection) / len(union) if union else 0.0
            similarities.append(similarity)
        
        return similarities
    
    def should_block_post(self, platform: str, new_content: str, recent_posts: List[str]) -> tuple[bool, str]:
        """Check if a post should be blocked due to repetition"""
        if not recent_posts:
            return False, "No recent posts to compare"
        
        try:
            from sentence_transformers import SentenceTransformer
            from sklearn.metrics.pairwise import cosine_similarity
            import numpy as np
            
            model = SentenceTransformer('all-MiniLM-L6-v2')
            new_embedding = model.encode([new_content])
            recent_embeddings = model.encode(recent_posts[-5:])  # Check last 5 posts
            
            similarities = cosine_similarity(new_embedding, recent_embeddings)[0]
            max_similarity = np.max(similarities)
            
            if max_similarity >= self.diversity_thresholds['similarity_block']:
                return True, f"Content too similar (similarity: {max_similarity:.2f}) to recent posts"
            
            return False, f"Content unique enough (similarity: {max_similarity:.2f})"
            
        except Exception as e:
            print(f"⚠️ Post blocking check failed: {e}")
            return False, "Unable to verify uniqueness"
    
    def get_diversity_report(self, platform_data: Dict[str, List[str]]) -> str:
        """Generate a comprehensive diversity report"""
        report = f"📊 Content Diversity Report\n"
        report += f"{'='*40}\n\n"
        
        for platform, posts in platform_data.items():
            if not posts:
                continue
            
            analysis = self.analyze_diversity(platform, posts)
            
            status_emoji = {
                'good': '✅',
                'warning': '⚠️',
                'critical': '❌',
                'no_data': '📭'
            }.get(analysis['status'], '❓')
            
            report += f"{status_emoji} {platform.upper()}\n"
            report += f"   Posts analyzed: {analysis['post_count']}\n"
            report += f"   Diversity score: {analysis['diversity_score']:.2f}\n"
            
            if analysis['themes']:
                theme_counts = Counter(analysis['themes'])
                top_theme = theme_counts.most_common(1)[0]
                report += f"   Top theme: {top_theme[0]} ({top_theme[1]} posts)\n"
            
            if analysis['issues']:
                report += f"   Issues: {len(analysis['issues'])}\n"
                for issue in analysis['issues']:
                    report += f"     - {issue}\n"
            
            if analysis['recommendations']:
                report += f"   Recommendations:\n"
                for rec in analysis['recommendations']:
                    report += f"     - {rec}\n"
            
            report += "\n"
        
        return report


# Global instance
_diversity_monitor = None

def get_diversity_monitor() -> ContentDiversityMonitor:
    """Get or create the global diversity monitor instance"""
    global _diversity_monitor
    if _diversity_monitor is None:
        _diversity_monitor = ContentDiversityMonitor()
    return _diversity_monitor
