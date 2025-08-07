from db.crud import get_trades_stats

class PerformanceMonitor:
    @staticmethod
    def generate_daily_report() -> dict:
        stats = get_trades_stats()
        return {
            'total_trades': stats['count'],
            'success_rate': stats['success'] / stats['count'] if stats['count'] > 0 else 0,
            'total_profit': stats['profit']
        }
