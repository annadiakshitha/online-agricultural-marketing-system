/* AgroConnect – reusable i18n. English text in templates is the key; no per-page switching code.
   Entry format: "English text": [Telugu, Hindi, Tamil, Kannada, Marathi]  (missing entries fall back to English).
   Product names / descriptions come from the database and stay in English. */
const I18N = (() => {
  const LANGS = { en: 'English', te: 'తెలుగు', hi: 'हिन्दी', ta: 'தமிழ்', kn: 'ಕನ್ನಡ', mr: 'मराठी' };
  const SHORT = { en: 'EN', te: 'తె', hi: 'हि', ta: 'த', kn: 'ಕ', mr: 'म' };
  const IDX = { te: 0, hi: 1, ta: 2, kn: 3, mr: 4 };

  const D = {
    /* Navigation */
    'Home': ['హోమ్', 'होम', 'முகப்பு', 'ಮುಖಪುಟ', 'मुख्यपृष्ठ'],
    'Shop': ['షాప్', 'दुकान', 'கடை', 'ಅಂಗಡಿ', 'दुकान'],
    'Categories': ['వర్గాలు', 'श्रेणियाँ', 'வகைகள்', 'ವರ್ಗಗಳು', 'श्रेणी'],
    'Farmers': ['రైతులు', 'किसान', 'விவசாயிகள்', 'ರೈತರು', 'शेतकरी'],
    'Deals': ['ఆఫర్లు', 'ऑफ़र', 'சலுகைகள்', 'ಕೊಡುಗೆಗಳು', 'ऑफर्स'],
    'About': ['మా గురించి', 'हमारे बारे में', 'எங்களைப் பற்றி', 'ನಮ್ಮ ಬಗ್ಗೆ', 'आमच्याबद्दल'],
    'Search': ['వెతకండి', 'खोजें', 'தேடு', 'ಹುಡುಕಿ', 'शोधा'],
    'Search products': ['ఉత్పత్తులను వెతకండి', 'उत्पाद खोजें', 'பொருட்களைத் தேடு', 'ಉತ್ಪನ್ನಗಳನ್ನು ಹುಡುಕಿ', 'उत्पादने शोधा'],
    'Search seeds, fertilizers, tools, sellers…': ['విత్తనాలు, ఎరువులు, పనిముట్లు, అమ్మకందారులను వెతకండి…', 'बीज, उर्वरक, औज़ार, विक्रेता खोजें…', 'விதைகள், உரங்கள், கருவிகள், விற்பனையாளர்களைத் தேடு…', 'ಬೀಜ, ಗೊಬ್ಬರ, ಉಪಕರಣ, ಮಾರಾಟಗಾರರನ್ನು ಹುಡುಕಿ…', 'बियाणे, खते, अवजारे, विक्रेते शोधा…'],
    'Wishlist': ['కోరికల జాబితా', 'पसंदीदा सूची', 'விருப்பப் பட்டியல்', 'ಇಷ್ಟದ ಪಟ್ಟಿ', 'आवडती यादी'],
    'Cart': ['కార్ట్', 'कार्ट', 'கூடை', 'ಕಾರ್ಟ್', 'कार्ट'],
    'Account': ['ఖాతా', 'खाता', 'கணக்கு', 'ಖಾತೆ', 'खाते'],
    'My Profile': ['నా ప్రొఫైల్', 'मेरी प्रोफ़ाइल', 'என் சுயவிவரம்', 'ನನ್ನ ಪ್ರೊಫೈಲ್', 'माझी प्रोफाइल'],
    'My Orders': ['నా ఆర్డర్లు', 'मेरे ऑर्डर', 'என் ஆர்டர்கள்', 'ನನ್ನ ಆರ್ಡರ್‌ಗಳು', 'माझ्या ऑर्डर्स'],
    'Seller Dashboard': ['సెల్లర్ డాష్‌బోర్డ్', 'विक्रेता डैशबोर्ड', 'விற்பனையாளர் டாஷ்போர்டு', 'ಮಾರಾಟಗಾರ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್', 'विक्रेता डॅशबोर्ड'],
    'Admin Dashboard': ['అడ్మిన్ డాష్‌బోర్డ్', 'एडमिन डैशबोर्ड', 'நிர்வாக டாஷ்போர்டு', 'ಅಡ್ಮಿನ್ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್', 'अ‍ॅडमिन डॅशबोर्ड'],
    'Logout': ['లాగ్ అవుట్', 'लॉग आउट', 'வெளியேறு', 'ಲಾಗ್ ಔಟ್', 'लॉग आउट'],
    'Login': ['లాగిన్', 'लॉगिन', 'உள்நுழை', 'ಲಾಗಿನ್', 'लॉगिन'],
    'Register': ['నమోదు', 'पंजीकरण', 'பதிவு', 'ನೋಂದಣಿ', 'नोंदणी'],

    /* Hero + trust */
    'Everything Farmers Need.': ['రైతులకు కావలసినవన్నీ.', 'किसानों को जो कुछ चाहिए, सब कुछ।', 'விவசாயிகளுக்குத் தேவையான அனைத்தும்.', 'ರೈತರಿಗೆ ಬೇಕಾದ ಎಲ್ಲವೂ.', 'शेतकऱ्यांना लागणारे सर्व काही.'],
    'One Powerful Marketplace.': ['ఒకే శక్తివంతమైన మార్కెట్‌ప్లేస్.', 'एक शक्तिशाली बाज़ार।', 'ஒரே சக்திவாய்ந்த சந்தை.', 'ಒಂದೇ ಶಕ್ತಿಶಾಲಿ ಮಾರುಕಟ್ಟೆ.', 'एकच शक्तिशाली बाजारपेठ.'],
    'Quality seeds, fertilizers, tools, irrigation equipment and agricultural essentials — all in one place.': ['నాణ్యమైన విత్తనాలు, ఎరువులు, పనిముట్లు, నీటిపారుదల పరికరాలు మరియు వ్యవసాయ అవసరాలు — అన్నీ ఒకే చోట.', 'गुणवत्तापूर्ण बीज, उर्वरक, औज़ार, सिंचाई उपकरण और कृषि की ज़रूरी चीज़ें — सब एक ही जगह।', 'தரமான விதைகள், உரங்கள், கருவிகள், நீர்ப்பாசன உபகரணங்கள் — அனைத்தும் ஒரே இடத்தில்.', 'ಗುಣಮಟ್ಟದ ಬೀಜ, ಗೊಬ್ಬರ, ಉಪಕರಣ, ನೀರಾವರಿ ಸಾಧನಗಳು — ಎಲ್ಲವೂ ಒಂದೇ ಸ್ಥಳದಲ್ಲಿ.', 'दर्जेदार बियाणे, खते, अवजारे, सिंचन साधने — सर्व एकाच ठिकाणी.'],
    'Shop Now': ['ఇప్పుడే కొనండి', 'अभी खरीदें', 'இப்போதே வாங்குங்கள்', 'ಈಗಲೇ ಖರೀದಿಸಿ', 'आताच खरेदी करा'],
    'Explore Categories': ['వర్గాలను చూడండి', 'श्रेणियाँ देखें', 'வகைகளைப் பாருங்கள்', 'ವರ್ಗಗಳನ್ನು ನೋಡಿ', 'श्रेणी पहा'],
    'Trusted by farmers across India': ['భారతదేశం అంతటా రైతుల నమ్మకం', 'पूरे भारत के किसानों का भरोसा', 'இந்தியா முழுவதும் விவசாயிகளின் நம்பிக்கை', 'ಭಾರತದಾದ್ಯಂತ ರೈತರ ವಿಶ್ವಾಸ', 'संपूर्ण भारतातील शेतकऱ्यांचा विश्वास'],
    'Farmers': ['రైతులు', 'किसान', 'விவசாயிகள்', 'ರೈತರು', 'शेतकरी'],
    'Products': ['ఉత్పత్తులు', 'उत्पाद', 'பொருட்கள்', 'ಉತ್ಪನ್ನಗಳು', 'उत्पादने'],
    'Verified Sellers': ['ధృవీకరించిన అమ్మకందారులు', 'सत्यापित विक्रेता', 'சரிபார்க்கப்பட்ட விற்பனையாளர்கள்', 'ಪರಿಶೀಲಿತ ಮಾರಾಟಗಾರರು', 'सत्यापित विक्रेते'],

    /* Sections */
    'Shop by Category': ['వర్గం వారీగా కొనండి', 'श्रेणी के अनुसार खरीदें', 'வகை வாரியாக வாங்குங்கள்', 'ವರ್ಗದ ಪ್ರಕಾರ ಖರೀದಿಸಿ', 'श्रेणीनुसार खरेदी करा'],
    'Featured Agricultural Products': ['ప్రత్యేక వ్యవసాయ ఉత్పత్తులు', 'विशेष कृषि उत्पाद', 'சிறப்பு வேளாண் பொருட்கள்', 'ವಿಶೇಷ ಕೃಷಿ ಉತ್ಪನ್ನಗಳು', 'निवडक कृषी उत्पादने'],
    'Why AgroConnect': ['ఎందుకు అగ్రోకనెక్ట్', 'एग्रोकनेक्ट क्यों', 'ஏன் அக்ரோகனெக்ட்', 'ಏಕೆ ಅಗ್ರೋಕನೆಕ್ಟ್', 'अ‍ॅग्रोकनेक्ट का'],
    'Farmer Stories': ['రైతుల కథలు', 'किसानों की कहानियाँ', 'விவசாயிகளின் கதைகள்', 'ರೈತರ ಕಥೆಗಳು', 'शेतकऱ्यांच्या कथा'],
    'Agricultural Insights': ['వ్యవసాయ సమాచారం', 'कृषि जानकारी', 'வேளாண் தகவல்கள்', 'ಕೃಷಿ ಮಾಹಿತಿ', 'कृषी माहिती'],
    'View All': ['అన్నీ చూడండి', 'सभी देखें', 'அனைத்தையும் காண்க', 'ಎಲ್ಲವನ್ನೂ ನೋಡಿ', 'सर्व पहा'],
    'Explore': ['చూడండి', 'देखें', 'பாருங்கள்', 'ನೋಡಿ', 'पहा'],
    'Shop Deals': ['ఆఫర్లు చూడండి', 'ऑफ़र देखें', 'சலுகைகளைப் பாருங்கள்', 'ಕೊಡುಗೆಗಳನ್ನು ನೋಡಿ', 'ऑफर्स पहा'],
    'Verified Products': ['ధృవీకరించిన ఉత్పత్తులు', 'सत्यापित उत्पाद'],
    'Trusted Sellers': ['నమ్మకమైన అమ్మకందారులు', 'भरोसेमंद विक्रेता'],
    'Secure Payments': ['సురక్షిత చెల్లింపులు', 'सुरक्षित भुगतान'],
    'Fast Delivery': ['వేగవంతమైన డెలివరీ', 'तेज़ डिलीवरी'],
    'Farmer-Friendly Pricing': ['రైతులకు అనుకూల ధరలు', 'किसान-अनुकूल कीमतें'],
    'Support': ['సహాయం', 'सहायता'],
    'Illustrative image': ['నమూనా చిత్రం', 'उदाहरण चित्र'],
    'Subscribe': ['సభ్యత్వం పొందండి', 'सब्सक्राइब करें', 'சந்தா', 'ಚಂದಾದಾರರಾಗಿ', 'सबस्क्राइब करा'],

    /* Product + shop */
    'Add to Cart': ['కార్ట్‌కు జోడించండి', 'कार्ट में जोड़ें', 'கூடையில் சேர்', 'ಕಾರ್ಟ್‌ಗೆ ಸೇರಿಸಿ', 'कार्टमध्ये जोडा'],
    'Buy Now': ['ఇప్పుడే కొనండి', 'अभी खरीदें', 'இப்போதே வாங்கு', 'ಈಗಲೇ ಖರೀದಿಸಿ', 'आता खरेदी करा'],
    'Out of Stock': ['స్టాక్ లేదు', 'स्टॉक में नहीं', 'இருப்பு இல்லை', 'ಸ್ಟಾಕ್ ಇಲ್ಲ', 'स्टॉक संपला'],
    'In Stock': ['స్టాక్ ఉంది', 'स्टॉक में है', 'இருப்பு உள்ளது', 'ಸ್ಟಾಕ್ ಇದೆ', 'स्टॉक उपलब्ध'],
    'Quick View': ['త్వరిత వీక్షణ', 'झलक देखें', 'விரைவுப் பார்வை', 'ತ್ವರಿತ ನೋಟ', 'झटपट पहा'],
    'All Agricultural Products': ['అన్ని వ్యవసాయ ఉత్పత్తులు', 'सभी कृषि उत्पाद', 'அனைத்து வேளாண் பொருட்கள்', 'ಎಲ್ಲಾ ಕೃಷಿ ಉತ್ಪನ್ನಗಳು', 'सर्व कृषी उत्पादने'],
    'Search by product, category, seller or tag': ['ఉత్పత్తి, వర్గం, అమ్మకందారు లేదా ట్యాగ్ ద్వారా వెతకండి', 'उत्पाद, श्रेणी, विक्रेता या टैग से खोजें'],
    'Filters': ['ఫిల్టర్లు', 'फ़िल्टर', 'வடிகட்டிகள்', 'ಫಿಲ್ಟರ್‌ಗಳು', 'फिल्टर'],
    'Reset': ['రీసెట్', 'रीसेट', 'மீட்டமை', 'ಮರುಹೊಂದಿಸಿ', 'रीसेट'],
    'Category': ['వర్గం', 'श्रेणी', 'வகை', 'ವರ್ಗ', 'श्रेणी'],
    'All categories': ['అన్ని వర్గాలు', 'सभी श्रेणियाँ'],
    'Price Range (₹)': ['ధర పరిధి (₹)', 'मूल्य सीमा (₹)'],
    'Brand': ['బ్రాండ్', 'ब्रांड'], 'All brands': ['అన్ని బ్రాండ్లు', 'सभी ब्रांड'],
    'Seller': ['అమ్మకందారు', 'विक्रेता'], 'All sellers': ['అందరు అమ్మకందారులు', 'सभी विक्रेता'],
    'Rating': ['రేటింగ్', 'रेटिंग'], 'Any rating': ['ఏ రేటింగ్ అయినా', 'कोई भी रेटिंग'],
    'Availability': ['లభ్యత', 'उपलब्धता'], 'In stock only': ['స్టాక్ ఉన్నవి మాత్రమే', 'केवल स्टॉक में'],
    'Preferences': ['ఎంపికలు', 'प्राथमिकताएँ'],
    'Organic products': ['సేంద్రీయ ఉత్పత్తులు', 'जैविक उत्पाद'],
    'On discount (15%+)': ['డిస్కౌంట్ (15%+)', 'छूट पर (15%+)'],
    'Show results': ['ఫలితాలు చూపు', 'परिणाम दिखाएँ'],
    'Featured': ['ప్రత్యేకం', 'विशेष'], 'Newest': ['కొత్తవి', 'नवीनतम'],
    'Price: Low to High': ['ధర: తక్కువ నుండి ఎక్కువ', 'कीमत: कम से ज़्यादा'],
    'Price: High to Low': ['ధర: ఎక్కువ నుండి తక్కువ', 'कीमत: ज़्यादा से कम'],
    'Highest Rated': ['అత్యధిక రేటింగ్', 'सबसे ज़्यादा रेटिंग'],
    'Biggest Discount': ['అత్యధిక డిస్కౌంట్', 'सबसे बड़ी छूट'],
    'No products found.': ['ఉత్పత్తులు కనబడలేదు.', 'कोई उत्पाद नहीं मिला।'],

    /* Cart + wishlist */
    'Shopping Cart': ['షాపింగ్ కార్ట్', 'शॉपिंग कार्ट', 'ஷாப்பிங் கூடை', 'ಶಾಪಿಂಗ್ ಕಾರ್ಟ್', 'शॉपिंग कार्ट'],
    'Your cart is empty': ['మీ కార్ట్ ఖాళీగా ఉంది', 'आपका कार्ट खाली है', 'உங்கள் கூடை காலியாக உள்ளது', 'ನಿಮ್ಮ ಕಾರ್ಟ್ ಖಾಲಿಯಾಗಿದೆ', 'तुमचा कार्ट रिकामा आहे'],
    'Order Summary': ['ఆర్డర్ సారాంశం', 'ऑर्डर सारांश', 'ஆர்டர் சுருக்கம்', 'ಆರ್ಡರ್ ಸಾರಾಂಶ', 'ऑर्डर सारांश'],
    'Subtotal': ['ఉప మొత్తం', 'उप-योग', 'கூட்டுத்தொகை', 'ಉಪಮೊತ್ತ', 'उप-बेरीज'],
    'Discount': ['డిస్కౌంట్', 'छूट', 'தள்ளுபடி', 'ರಿಯಾಯಿತಿ', 'सवलत'],
    'Delivery': ['డెలివరీ', 'डिलीवरी', 'டெலிவரி', 'ಡೆಲಿವರಿ', 'डिलिव्हरी'],
    'Tax': ['పన్ను', 'कर', 'வரி', 'ತೆರಿಗೆ', 'कर'],
    'GST (5%)': ['జీఎస్టీ (5%)', 'जीएसटी (5%)'],
    'Total': ['మొత్తం', 'कुल', 'மொத்தம்', 'ಒಟ್ಟು', 'एकूण'],
    'Proceed to Checkout': ['చెక్‌అవుట్‌కు వెళ్లండి', 'चेकआउट पर जाएँ', 'செக்அவுட்டுக்குச் செல்', 'ಚೆಕ್‌ಔಟ್‌ಗೆ ಮುಂದುವರಿಯಿರಿ', 'चेकआउटकडे जा'],
    'My Wishlist': ['నా కోరికల జాబితా', 'मेरी पसंदीदा सूची'],
    'Your wishlist is empty': ['మీ కోరికల జాబితా ఖాళీగా ఉంది', 'आपकी पसंदीदा सूची खाली है'],
    'Remove': ['తొలగించు', 'हटाएँ'], 'Move to Cart': ['కార్ట్‌కు తరలించు', 'कार्ट में ले जाएँ'],
    'Browse Products': ['ఉత్పత్తులను చూడండి', 'उत्पाद देखें'],

    /* Checkout + auth */
    'Checkout': ['చెక్‌అవుట్', 'चेकआउट', 'செக்அவுட்', 'ಚೆಕ್‌ಔಟ್', 'चेकआउट'],
    'Customer Information': ['కస్టమర్ సమాచారం', 'ग्राहक जानकारी'],
    'Delivery Address': ['డెలివరీ చిరునామా', 'डिलीवरी पता'],
    'Payment': ['చెల్లింపు', 'भुगतान', 'கட்டணம்', 'ಪಾವತಿ', 'पेमेंट'],
    'Order Review': ['ఆర్డర్ సమీక్ష', 'ऑर्डर समीक्षा'],
    'Information': ['సమాచారం', 'जानकारी'], 'Address': ['చిరునామా', 'पता'], 'Review': ['సమీక్ష', 'समीक्षा'],
    'Credit / Debit Card': ['క్రెడిట్ / డెబిట్ కార్డ్', 'क्रेडिट / डेबिट कार्ड'],
    'Cash on Delivery': ['క్యాష్ ఆన్ డెలివరీ', 'कैश ऑन डिलीवरी'],
    'Place Order': ['ఆర్డర్ చేయండి', 'ऑर्डर करें', 'ஆர்டர் செய்', 'ಆರ್ಡರ್ ಮಾಡಿ', 'ऑर्डर करा'],
    'Continue': ['కొనసాగించు', 'जारी रखें'], 'Back': ['వెనుకకు', 'वापस'],
    'Full Name': ['పూర్తి పేరు', 'पूरा नाम'], 'Email': ['ఈమెయిల్', 'ईमेल'], 'Mobile Number': ['మొబైల్ నంబర్', 'मोबाइल नंबर'],
    'Pincode': ['పిన్‌కోడ్', 'पिनकोड'], 'District': ['జిల్లా', 'ज़िला'], 'State': ['రాష్ట్రం', 'राज्य'],
    'Password': ['పాస్‌వర్డ్', 'पासवर्ड', 'கடவுச்சொல்', 'ಪಾಸ್‌ವರ್ಡ್', 'पासवर्ड'],
    'Create account': ['ఖాతా సృష్టించండి', 'खाता बनाएँ'], 'Create Account': ['ఖాతా సృష్టించండి', 'खाता बनाएँ'],
    'Welcome back to AgroConnect': ['అగ్రోకనెక్ట్‌కు తిరిగి స్వాగతం', 'एग्रोकनेक्ट में वापसी पर स्वागत है'],
    'Demo accounts': ['డెమో ఖాతాలు', 'डेमो खाते'],
    'Customer': ['కస్టమర్', 'ग्राहक'], 'Admin': ['అడ్మిన్', 'एडमिन'],

    /* Orders */
    'Order Placed': ['ఆర్డర్ చేయబడింది', 'ऑर्डर दिया गया'], 'Confirmed': ['నిర్ధారించబడింది', 'पुष्टि हुई'],
    'Packed': ['ప్యాక్ చేయబడింది', 'पैक किया गया'], 'Shipped': ['పంపబడింది', 'भेजा गया'],
    'Out for Delivery': ['డెలివరీకి బయలుదేరింది', 'डिलीवरी के लिए निकला'], 'Delivered': ['డెలివరీ అయింది', 'पहुँचा दिया गया'],

    /* Assistant + order map */
    'Ask AI': ['AI అడగండి', 'AI से पूछें', 'AI-யிடம் கேள்', 'AI ಕೇಳಿ', 'AI ला विचारा'],
    'AgroConnect Assistant': ['అగ్రోకనెక్ట్ సహాయకుడు', 'एग्रोकनेक्ट सहायक', 'அக்ரோகனெக்ட் உதவியாளர்', 'ಅಗ್ರೋಕನೆಕ್ಟ್ ಸಹಾಯಕ', 'अ‍ॅग्रोकनेक्ट सहाय्यक'],
    'Ask about products, crops, delivery…': ['ఉత్పత్తులు, పంటలు, డెలివరీ గురించి అడగండి…', 'उत्पाद, फसल, डिलीवरी के बारे में पूछें…', 'பொருட்கள், பயிர்கள், டெலிவரி பற்றி கேளுங்கள்…', 'ಉತ್ಪನ್ನ, ಬೆಳೆ, ಡೆಲಿವರಿ ಬಗ್ಗೆ ಕೇಳಿ…', 'उत्पादने, पिके, डिलिव्हरी बद्दल विचारा…'],
    "Hi! I'm your AgroConnect assistant. Ask me about products, farming tips, delivery or your orders.": ['నమస్తే! నేను మీ అగ్రోకనెక్ట్ సహాయకుడిని. ఉత్పత్తులు, వ్యవసాయ చిట్కాలు, డెలివరీ లేదా మీ ఆర్డర్ల గురించి అడగండి.', 'नमस्ते! मैं आपका एग्रोकनेक्ट सहायक हूँ। उत्पाद, खेती के सुझाव, डिलीवरी या अपने ऑर्डर के बारे में पूछें।'],
    'Track on Map': ['మ్యాప్‌లో ట్రాక్ చేయండి', 'नक्शे पर ट्रैक करें', 'வரைபடத்தில் கண்காணி', 'ನಕ್ಷೆಯಲ್ಲಿ ಟ್ರ್ಯಾಕ್ ಮಾಡಿ', 'नकाशावर ट्रॅक करा'],
    'My location': ['నా స్థానం', 'मेरा स्थान', 'என் இடம்', 'ನನ್ನ ಸ್ಥಳ', 'माझे स्थान'],
    'Status': ['స్థితి', 'स्थिति', 'நிலை', 'ಸ್ಥಿತಿ', 'स्थिती'],
    'Now at': ['ప్రస్తుతం', 'अभी यहाँ', 'தற்போது', 'ಈಗ ಇರುವುದು', 'सध्या येथे'],
    'Distance': ['దూరం', 'दूरी', 'தூரம்', 'ದೂರ', 'अंतर'],
    'Estimated delivery': ['అంచనా డెలివరీ', 'अनुमानित डिलीवरी', 'மதிப்பிடப்பட்ட டெலிவரி', 'ಅಂದಾಜು ಡೆಲಿವರಿ', 'अंदाजे डिलिव्हरी'],
    /* Farmer tools, rentals, coupons, interfaces */
    'Farmer Tools': ['రైతు సాధనాలు', 'किसान उपकरण', 'விவசாயி கருவிகள்', 'ರೈತ ಸಾಧನಗಳು', 'शेतकरी साधने'],
    'Farmer Dashboard': ['రైతు డాష్‌బోర్డ్', 'किसान डैशबोर्ड', 'விவசாயி டாஷ்போர்டு', 'ರೈತ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್', 'शेतकरी डॅशबोर्ड'],
    'Farmer': ['రైతు', 'किसान', 'விவசாயி', 'ರೈತ', 'शेतकरी'],
    'Seller': ['అమ్మకందారు', 'विक्रेता', 'விற்பனையாளர்', 'ಮಾರಾಟಗಾರ', 'विक्रेता'],
    'Choose Your Interface': ['మీ ఇంటర్‌ఫేస్‌ను ఎంచుకోండి', 'अपना इंटरफ़ेस चुनें', 'உங்கள் இடைமுகத்தைத் தேர்ந்தெடுங்கள்', 'ನಿಮ್ಮ ಇಂಟರ್‌ಫೇಸ್ ಆಯ್ಕೆಮಾಡಿ', 'तुमचा इंटरफेस निवडा'],
    'Join as Customer': ['కస్టమర్‌గా చేరండి', 'ग्राहक के रूप में जुड़ें'], 'Join as Farmer': ['రైతుగా చేరండి', 'किसान के रूप में जुड़ें'], 'Join as Seller': ['అమ్మకందారుగా చేరండి', 'विक्रेता के रूप में जुड़ें'],
    'Start shopping': ['షాపింగ్ ప్రారంభించండి', 'खरीदारी शुरू करें'], 'Open farmer dashboard': ['రైతు డాష్‌బోర్డ్ తెరవండి', 'किसान डैशबोर्ड खोलें'], 'Open seller dashboard': ['సెల్లర్ డాష్‌బోర్డ్ తెరవండి', 'विक्रेता डैशबोर्ड खोलें'],
    'Crop Doctor': ['పంట వైద్యుడు', 'फसल डॉक्टर', 'பயிர் மருத்துவர்', 'ಬೆಳೆ ವೈದ್ಯ', 'पीक डॉक्टर'],
    'Check my crop': ['నా పంటను పరీక్షించండి', 'मेरी फसल जाँचें'],
    'Equipment Rental': ['పరికరాల అద్దె', 'उपकरण किराया', 'உபகரண வாடகை', 'ಉಪಕರಣ ಬಾಡಿಗೆ', 'उपकरण भाडे'],
    'Rent Equipment': ['పరికరాలు అద్దెకు తీసుకోండి', 'उपकरण किराए पर लें'], 'Rent Farm Equipment': ['వ్యవసాయ పరికరాలు అద్దెకు', 'कृषि उपकरण किराए पर'],
    'My Rentals': ['నా అద్దెలు', 'मेरे किराये'], 'Manage Rentals': ['అద్దెలను నిర్వహించండి', 'किराये प्रबंधित करें'],
    'Request booking': ['బుకింగ్ అభ్యర్థన', 'बुकिंग अनुरोध'], 'Book this equipment': ['ఈ పరికరాన్ని బుక్ చేయండి', 'यह उपकरण बुक करें'],
    'Weather & Advisory': ['వాతావరణం & సలహా', 'मौसम और सलाह'], 'Weather & Farm Advisory': ['వాతావరణం & వ్యవసాయ సలహా', 'मौसम और कृषि सलाह'], 'Weather': ['వాతావరణం', 'मौसम'],
    'Farm advisory': ['వ్యవసాయ సలహా', 'कृषि सलाह'], 'Quick actions': ['త్వరిత చర్యలు', 'त्वरित कार्य'],
    'Fertilizer Calculator': ['ఎరువుల కాలిక్యులేటర్', 'उर्वरक कैलकुलेटर', 'உர கணிப்பான்', 'ಗೊಬ್ಬರ ಕ್ಯಾಲ್ಕುಲೇಟರ್', 'खत कॅल्क्युलेटर'],
    'Calculate': ['లెక్కించండి', 'गणना करें'], 'Fertilizer required': ['అవసరమైన ఎరువులు', 'आवश्यक उर्वरक'], 'When to apply': ['ఎప్పుడు వేయాలి', 'कब डालें'],
    'Have a coupon?': ['కూపన్ ఉందా?', 'कूपन है?'], 'Apply': ['వర్తింపజేయి', 'लागू करें'], 'Download Invoice': ['ఇన్వాయిస్ డౌన్‌లోడ్', 'इनवॉइस डाउनलोड करें'],
    'Possible causes': ['సాధ్యమైన కారణాలు', 'संभावित कारण'], 'What to do': ['ఏమి చేయాలి', 'क्या करें'], 'Prevention': ['నివారణ', 'रोकथाम'],
    /* Footer */
    'Customer Support': ['కస్టమర్ సహాయం', 'ग्राहक सहायता'], 'For Farmers': ['రైతుల కోసం', 'किसानों के लिए'],
    'Company': ['సంస్థ', 'कंपनी'], 'Follow Us': ['మమ్మల్ని అనుసరించండి', 'हमें फ़ॉलो करें'],
    'Help Center': ['సహాయ కేంద్రం', 'सहायता केंद्र'], 'Shipping': ['షిప్పింగ్', 'शिपिंग'], 'Returns': ['రిటర్నులు', 'वापसी'],
    'Track Order': ['ఆర్డర్ ట్రాక్ చేయండి', 'ऑर्डर ट्रैक करें'], 'Become a Seller': ['అమ్మకందారు అవ్వండి', 'विक्रेता बनें'],
    'Privacy Policy': ['గోప్యతా విధానం', 'गोपनीयता नीति'], 'Terms': ['నిబంధనలు', 'शर्तें'],
    'Contact': ['సంప్రదించండి', 'संपर्क'], 'About us': ['మా గురించి', 'हमारे बारे में'], 'Careers': ['ఉద్యోగాలు', 'करियर'],
    'Empowering Farmers. Connecting Markets.': ['రైతులకు శక్తి. మార్కెట్లతో అనుసంధానం.', 'किसानों को सशक्त बनाना। बाज़ारों से जोड़ना।'],
    'Seeds': ['విత్తనాలు', 'बीज', 'விதைகள்', 'ಬೀಜಗಳು', 'बियाणे'],
    'Fertilizers': ['ఎరువులు', 'उर्वरक', 'உரங்கள்', 'ಗೊಬ್ಬರಗಳು', 'खते'],
    'Crop Protection': ['పంట రక్షణ', 'फसल सुरक्षा'], 'Irrigation': ['నీటిపారుదల', 'सिंचाई'],
    'Farming Tools': ['వ్యవసాయ పనిముట్లు', 'कृषि औज़ार'], 'Tools': ['పనిముట్లు', 'औज़ार'],
    'Machinery': ['యంత్రాలు', 'मशीनरी'], 'Organic Products': ['సేంద్రీయ ఉత్పత్తులు', 'जैविक उत्पाद'],
    'Animal Feed': ['పశుగ్రాసం', 'पशु आहार'],
  };

  /* Messages with a variable part, e.g. toasts */
  const M = {
    'added_cart': { en: '{name} added to cart', te: '{name} కార్ట్‌కు జోడించబడింది', hi: '{name} कार्ट में जोड़ा गया', ta: '{name} கூடையில் சேர்க்கப்பட்டது', kn: '{name} ಕಾರ್ಟ್‌ಗೆ ಸೇರಿಸಲಾಗಿದೆ', mr: '{name} कार्टमध्ये जोडले' },
    'removed_cart': { en: '{name} removed from cart', te: '{name} కార్ట్ నుండి తొలగించబడింది', hi: '{name} कार्ट से हटाया गया', ta: '{name} கூடையிலிருந்து நீக்கப்பட்டது', kn: '{name} ಕಾರ್ಟ್‌ನಿಂದ ತೆಗೆಯಲಾಗಿದೆ', mr: '{name} कार्टमधून काढले' },
    'added_wish': { en: '{name} added to wishlist', te: '{name} కోరికల జాబితాకు జోడించబడింది', hi: '{name} पसंदीदा सूची में जोड़ा गया', ta: '{name} விருப்பப் பட்டியலில் சேர்க்கப்பட்டது', kn: '{name} ಇಷ್ಟದ ಪಟ್ಟಿಗೆ ಸೇರಿಸಲಾಗಿದೆ', mr: '{name} आवडत्या यादीत जोडले' },
    'removed_wish': { en: '{name} removed from wishlist', te: '{name} కోరికల జాబితా నుండి తొలగించబడింది', hi: '{name} पसंदीदा सूची से हटाया गया', ta: '{name} விருப்பப் பட்டியலிலிருந்து நீக்கப்பட்டது', kn: '{name} ಇಷ್ಟದ ಪಟ್ಟಿಯಿಂದ ತೆಗೆಯಲಾಗಿದೆ', mr: '{name} आवडत्या यादीतून काढले' },
    'lang_changed': { en: 'Language changed to {name}', te: 'భాష {name}కి మార్చబడింది', hi: 'भाषा {name} में बदली गई', ta: 'மொழி {name} ஆக மாற்றப்பட்டது', kn: 'ಭಾಷೆಯನ್ನು {name}ಗೆ ಬದಲಾಯಿಸಲಾಗಿದೆ', mr: 'भाषा {name} मध्ये बदलली' },
    'order_ok': { en: 'Order placed successfully', te: 'ఆర్డర్ విజయవంతంగా చేయబడింది', hi: 'ऑर्डर सफलतापूर्वक दिया गया', ta: 'ஆர்டர் வெற்றிகரமாக செய்யப்பட்டது', kn: 'ಆರ್ಡರ್ ಯಶಸ್ವಿಯಾಗಿ ಮಾಡಲಾಗಿದೆ', mr: 'ऑर्डर यशस्वीरित्या दिला' },
  };

  const ATTRS = ['placeholder', 'aria-label', 'title'];
  let lang = 'en';
  try { lang = localStorage.getItem('language') || 'en'; } catch (e) {}
  if (!LANGS[lang]) lang = 'en';

  const lookup = (text, l) => {
    if (l === 'en') return null;
    const star = /\s*\*\s*$/.test(text) ? ' *' : '';
    const key = text.replace(/\s*\*\s*$/, '').trim();
    const row = D[key]; const out = row && row[IDX[l]];
    return out ? out + star : null;
  };

  function translateText(node, l) {
    const raw = node.__orig !== undefined ? node.__orig : node.nodeValue;
    const trimmed = raw.trim();
    if (!trimmed) return;
    const out = lookup(trimmed, l);
    if (out) { if (node.__orig === undefined) node.__orig = raw; node.nodeValue = raw.replace(trimmed, out); }
    else if (node.__orig !== undefined) { node.nodeValue = node.__orig; }
  }

  function translateEl(el, l) {
    ATTRS.forEach(a => {
      if (!el.hasAttribute || !el.hasAttribute(a)) return;
      const k = 'orig' + a.replace(/-./g, m => m[1].toUpperCase());
      const raw = el.dataset[k] !== undefined ? el.dataset[k] : el.getAttribute(a);
      const out = lookup(raw, l);
      if (out) { el.dataset[k] = raw; el.setAttribute(a, out); } else if (el.dataset[k] !== undefined) el.setAttribute(a, el.dataset[k]);
    });
  }

  function apply(root = document.body, l = lang) {
    if (!root) return;
    if (root.nodeType === 3) { translateText(root, l); return; }
    if (root.nodeType !== 1) return;
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT | NodeFilter.SHOW_TEXT);
    let n = walker.currentNode;
    const skip = el => /^(SCRIPT|STYLE|TEXTAREA|CODE)$/.test(el.tagName) || el.hasAttribute('data-no-i18n');
    while (n) {
      if (n.nodeType === 3) { if (!skip(n.parentElement)) translateText(n, l); }
      else { if (skip(n)) { n = walker.nextSibling() || null; continue; } translateEl(n, l); }
      n = walker.nextNode();
    }
  }

  const t = (key, vars = {}) => {
    const m = M[key]; let s = (m && (m[lang] || m.en)) || key;
    return s.replace(/\{(\w+)\}/g, (_, v) => vars[v] ?? '');
  };

  function setLang(l, announce = true) {
    if (!LANGS[l]) return;
    lang = l;
    try { localStorage.setItem('language', l); } catch (e) {}
    document.documentElement.lang = l;
    apply(document.body, l);
    document.querySelectorAll('[data-lang-label]').forEach(el => { el.textContent = SHORT[l]; });
    document.querySelectorAll('.lang-opt').forEach(b => { b.classList.toggle('active', b.dataset.lang === l); b.setAttribute('aria-checked', b.dataset.lang === l); });
    if (announce && typeof toast === 'function') toast(t('lang_changed', { name: LANGS[l] }));
  }

  function init() {
    const menu = document.getElementById('langMenu');
    if (menu) {
      const dd = document.getElementById('langDropdown'), btn = document.getElementById('langBtn');
      dd.innerHTML = Object.entries(LANGS).map(([c, n]) => `<button type="button" class="lang-opt" role="menuitemradio" data-lang="${c}" data-no-i18n>${n}</button>`).join('');
      btn.addEventListener('click', e => { e.stopPropagation(); const o = dd.classList.toggle('open'); btn.setAttribute('aria-expanded', o); });
      dd.addEventListener('click', e => { const b = e.target.closest('.lang-opt'); if (b) { setLang(b.dataset.lang); dd.classList.remove('open'); btn.setAttribute('aria-expanded', false); } });
      document.addEventListener('click', () => { dd.classList.remove('open'); btn.setAttribute('aria-expanded', false); });
    }
    setLang(lang, false);
    // Translate content added later (product cards, cart rows, modals…)
    new MutationObserver(muts => muts.forEach(m => m.addedNodes.forEach(n => { if (lang !== 'en') apply(n, lang); })))
      .observe(document.body, { childList: true, subtree: true });
  }

  document.addEventListener('DOMContentLoaded', init);
  return { t, setLang, apply, LANGS, get lang() { return lang; } };
})();

window.I18N = I18N;
