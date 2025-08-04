ARABIC_MESSAGES = {
    'welcome': "👋 أهلاً بك في بوت التداول الذكي للعملات الرقمية!\n\n"
               "🎯 هذا البوت يساعدك في تحقيق أرباح آمنة من خلال تقنيات المراجحة الآلية.\n\n"
               "📌 الرجاء اختيار أحد الخيارات من القائمة أدناه:",
    
    'main_menu': "🏠 القائمة الرئيسية\n\n"
                "اختر أحد الخيارات التالية:",
    
    'no_opportunities': "⚠️ لا توجد فرص استثمارية متاحة حالياً.\n"
                       "سيقوم البوت بإعلامك عند ظهور فرص جديدة.",
    
    'opportunities_header': "🔍 أفضل الفرص الاستثمارية المتاحة الآن:\n\n",
    
    'opportunity_item': "{index}. {description}\n"
                       "📈 الربح المتوقع: {profit}%\n"
                       "🛡️ الحماية: 100% ضد الخسارة\n\n",
    
    'report_period_prompt': "📅 اختر الفترة الزمنية للتقرير:\n"
                           "أو حدد فترة مخصصة:",
    
    'report_header': "📊 تقرير أداء الاستثمار\n"
                    "الفترة من {start} إلى {end}\n\n",
    
    'report_content': "• عدد الصفقات: {trades}\n"
                     "• إجمالي المبلغ المستثمر: {invested:.2f} USDT\n"
                     "• إجمالي الأرباح: {profit:.2f} USDT\n"
                     "• معدل النجاح: {rate}\n\n"
                     "💡 نصيحة: {advice}",
    
    'report_error': "⚠️ حدث خطأ أثناء إنشاء التقرير. يرجى المحاولة لاحقاً.",
    
    'wallet_summary': "💼 ملخص محفظتك\n\n"
                    "• الرصيد المتاح: {balance:.2f} USDT\n"
                    "• إجمالي الاستثمارات النشطة: {active_investments:.2f} USDT\n"
                    "• إجمالي الأرباح هذا الشهر: {monthly_profit:.2f} USDT\n\n"
                    "لإيداع أو سحب أموال، استخدم الأزرار أدناه:",
    
    'investment_guide': "📚 دليل الاستثمار الآمن\n\n"
                      "1. اختر الفرص ذات الربح المتوقع فوق 3%\n"
                      "2. وزع استثماراتك على عدة فرص\n"
                      "3. استخدم خاصية الاستثمار المستمر\n\n"
                      "🛡️ جميع استثماراتك مؤمنة ضد الخسارة",
    
    # ... المزيد من الرسائل ...
}

def get_message(key, lang='ar', **kwargs):
    messages = ARABIC_MESSAGES if lang == 'ar' else ENGLISH_MESSAGES
    return messages.get(key, '').format(**kwargs)
