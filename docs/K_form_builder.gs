/**
 * Creates a bilingual, anonymous HeatShield student survey and a separate
 * pilot sign-up form. Run in Apps Script; generated links are logged for the
 * team and must be kept private. No form IDs or secrets are stored here.
 */
function buildHeatShieldSurveyForms() {
  const signupForm = FormApp.create('HeatShield student pilot sign-up / HeatShield विद्यार्थी पायलट साइन-अप');
  signupForm
    .setDescription(
      'Optional sign-up for the HeatShield student pilot. This is separate from the anonymous survey; do not include survey answers here.\n\n' +
      'HeatShield विद्यार्थी पायलट के लिए वैकल्पिक साइन-अप। यह गुमनाम सर्वेक्षण से अलग है; यहाँ सर्वेक्षण के उत्तर न लिखें।'
    )
    .setPublished(true)
    .setAcceptingResponses(true)
    .setCollectEmail(false)
    .setLimitOneResponsePerUser(false)
    .setConfirmationMessage(
      'Thank you. Your sign-up is stored separately from survey answers. / धन्यवाद। आपका साइन-अप सर्वेक्षण के उत्तरों से अलग रखा जाता है।'
    );

  signupForm.addCheckboxItem()
    .setTitle('I agree to be contacted about the student pilot. / मैं विद्यार्थी पायलट के बारे में संपर्क किए जाने की सहमति देता/देती हूँ।')
    .setChoiceValues(['Yes, contact me / हाँ, मुझसे संपर्क करें'])
    .setRequired(true);

  const emailItem = signupForm.addTextItem()
    .setTitle('Email address for pilot contact / पायलट के लिए ईमेल पता')
    .setHelpText('This contact detail is collected only in this separate sign-up form. / यह संपर्क जानकारी केवल इस अलग साइन-अप फ़ॉर्म में ली जाती है।')
    .setRequired(true);
  emailItem.setValidation(
    FormApp.createTextValidation()
      .requireTextIsEmail()
      .setHelpText('Enter a valid email address. / सही ईमेल पता लिखें।')
      .build()
  );

  const surveyForm = FormApp.create('HeatShield student heat-experience survey / HeatShield विद्यार्थी गर्मी-अनुभव सर्वेक्षण');
  surveyForm
    .setDescription(
      'We are a student team in the Global Sustainability Challenge. This voluntary, anonymous survey is for college students aged 18 or older and takes about 4 minutes. We do not ask for names, roll numbers, phone numbers, or emails. You may stop at any time. This is not medical advice. An optional pilot sign-up link appears at the end in a separate form; it is not linked to your answers.\n\n' +
      'हम Global Sustainability Challenge में भाग लेने वाली विद्यार्थियों की टीम हैं। यह स्वैच्छिक, गुमनाम सर्वेक्षण 18 वर्ष या उससे अधिक आयु के कॉलेज विद्यार्थियों के लिए है और इसमें लगभग 4 मिनट लगते हैं। हम नाम, रोल नंबर, फ़ोन नंबर या ईमेल नहीं माँगते। आप किसी भी समय रुक सकते हैं। यह चिकित्सा सलाह नहीं है। अंत में अलग फ़ॉर्म का वैकल्पिक पायलट-साइन-अप लिंक दिया जाएगा; उसका आपके उत्तरों से लिंक नहीं है।'
    )
    .setPublished(true)
    .setAcceptingResponses(true)
    .setCollectEmail(false)
    .setLimitOneResponsePerUser(false)
    .setProgressBar(true)
    .setShuffleQuestions(false)
    .setConfirmationMessage(
      'Thank you for sharing your experience. / अपना अनुभव साझा करने के लिए धन्यवाद।'
    );

  const ageGate = surveyForm.addMultipleChoiceItem()
    .setTitle('Are you 18 years old or older? / क्या आपकी आयु 18 वर्ष या उससे अधिक है?')
    .setRequired(true);

  const notEligiblePage = surveyForm.addPageBreakItem()
    .setTitle('Thank you / धन्यवाद')
    .setHelpText(
      'This survey is only for people aged 18 or older. It ends here; no research questions will be shown. / यह सर्वेक्षण केवल 18 वर्ष या उससे अधिक आयु के लोगों के लिए है। यह यहीं समाप्त होता है; शोध संबंधी प्रश्न नहीं दिखाए जाएँगे।'
    )
    .setGoToPage(FormApp.PageNavigationType.SUBMIT);

  const consentPage = surveyForm.addPageBreakItem()
    .setTitle('Consent / सहमति')
    .setHelpText('Taking part is voluntary. Close the form if you do not agree. / भाग लेना स्वैच्छिक है। सहमत न हों तो फ़ॉर्म बंद कर दें।');

  surveyForm.addCheckboxItem()
    .setTitle('I have read the information above and voluntarily agree to take this anonymous survey. / मैंने ऊपर दी गई जानकारी पढ़ ली है और इस गुमनाम सर्वेक्षण में स्वेच्छा से भाग लेने के लिए सहमत हूँ।')
    .setChoiceValues([
      'I agree / मैं सहमत हूँ'
    ])
    .setRequired(true);

  const surveyStart = surveyForm.addPageBreakItem()
    .setTitle('Student experience / विद्यार्थी अनुभव')
    .setHelpText('Please answer about your own college experience. / कृपया अपने कॉलेज के अनुभव के बारे में उत्तर दें।');

  ageGate.setChoices([
    ageGate.createChoice('Yes, I am 18 or older / हाँ, मेरी आयु 18 वर्ष या उससे अधिक है', consentPage),
    ageGate.createChoice('No, I am under 18 / नहीं, मेरी आयु 18 वर्ष से कम है', notEligiblePage)
  ]);

  addCheckboxQuestion(
    surveyForm,
    '1. Which student groups apply to you? Select all that apply. / आप पर कौन-से विद्यार्थी समूह लागू होते हैं? सभी लागू विकल्प चुनें।',
    [
      'DTU day scholar/commuter / DTU डे-स्कॉलर/आने-जाने वाले विद्यार्थी',
      'DTU hostel resident / DTU हॉस्टल निवासी',
      'DTU student in outdoor-heavy activities (sports, NCC/NSS, fieldwork, workshops, fest volunteering) / DTU में बाहर अधिक समय वाली गतिविधियों के विद्यार्थी',
      'DTU student with outdoor part-time work (for example, gig delivery, event staff, or commuting tutor) / DTU में बाहर किया जाने वाला पार्ट-टाइम काम (जैसे गिग डिलीवरी, कार्यक्रम-कर्मी या आने-जाने वाले ट्यूटर)',
      'Student at another Delhi-NCR college (comparison group) / दिल्ली-NCR के अन्य कॉलेज का विद्यार्थी (तुलना समूह)'
    ],
    true,
    'Select each DTU group that fits you. Do not select an “other college” option together with DTU. / DTU के सभी लागू समूह चुनें। DTU के साथ “अन्य कॉलेज” विकल्प न चुनें।'
  );

  addMultipleChoiceQuestion(
    surveyForm,
    '2. During the college term, where do you live? / कॉलेज सत्र के दौरान आप कहाँ रहते हैं?',
    [
      'Day scholar/commuter / डे-स्कॉलर/आना-जाना',
      'College hostel / कॉलेज हॉस्टल',
      'Other arrangement / अन्य व्यवस्था',
      'Prefer not to say / बताना नहीं चाहते'
    ],
    true
  );

  addMultipleChoiceQuestion(
    surveyForm,
    '3. What best describes your usual one-way trip to campus (mode and time)? / परिसर तक आपकी आमतौर पर एक तरफ़ की यात्रा (साधन और समय) का सबसे सही वर्णन कौन-सा है?',
    [
      'Walk/cycle, 15 minutes or less / पैदल/साइकिल, 15 मिनट या कम',
      'Walk/cycle, 16–30 minutes / पैदल/साइकिल, 16–30 मिनट',
      'Walk/cycle, over 30 minutes / पैदल/साइकिल, 30 मिनट से अधिक',
      'Metro/bus, under 30 minutes / मेट्रो/बस, 30 मिनट से कम',
      'Metro/bus, 30–60 minutes / मेट्रो/बस, 30–60 मिनट',
      'Metro/bus, over 60 minutes / मेट्रो/बस, 60 मिनट से अधिक',
      'Auto/2-wheeler/car, under 30 minutes / ऑटो/दोपहिया/कार, 30 मिनट से कम',
      'Auto/2-wheeler/car, 30–60 minutes / ऑटो/दोपहिया/कार, 30–60 मिनट',
      'Auto/2-wheeler/car, over 60 minutes / ऑटो/दोपहिया/कार, 60 मिनट से अधिक',
      'Mixed modes, under 30 minutes / कई साधन, 30 मिनट से कम',
      'Mixed modes, 30–60 minutes / कई साधन, 30–60 मिनट',
      'Mixed modes, over 60 minutes / कई साधन, 60 मिनट से अधिक',
      'No regular campus commute / परिसर तक नियमित यात्रा नहीं',
      'Prefer not to say / बताना नहीं चाहते'
    ],
    true
  );

  addCheckboxQuestion(
    surveyForm,
    '4. At what times are you usually outdoors on a college day? Select all that apply. / कॉलेज के दिन आप आमतौर पर किन समयों में बाहर रहते हैं? सभी लागू विकल्प चुनें।',
    [
      'Before 9 am / सुबह 9 बजे से पहले',
      '9 am–12 pm / सुबह 9–12',
      '12–3 pm / दोपहर 12–3',
      '3–6 pm / दोपहर 3–6',
      'After 6 pm / शाम 6 बजे के बाद',
      'It varies / समय बदलता रहता है',
      'I am not usually outdoors on a college day / कॉलेज के दिन मैं आमतौर पर बाहर नहीं रहता/रहती'
    ],
    true
  );

  addMultipleChoiceQuestion(
    surveyForm,
    '5. In April–June 2026, how often do you walk outdoors between buildings from 11 am to 3 pm? / अप्रैल–जून 2026 में सुबह 11 से दोपहर 3 बजे के बीच आप इमारतों के बीच बाहर पैदल कितनी बार जाते हैं?',
    [
      'Many times a day / दिन में कई बार',
      'About once a day / लगभग दिन में एक बार',
      'A few days a week / सप्ताह में कुछ दिन',
      'Rarely or never / बहुत कम या कभी नहीं',
      'Not applicable / लागू नहीं'
    ],
    true
  );

  surveyForm.addGridItem()
    .setTitle('6. When on campus, how often can you access these when needed? / परिसर में ज़रूरत पड़ने पर इन सुविधाओं तक आपकी पहुँच कितनी बार होती है?')
    .setHelpText('Choose one answer in each row. / हर पंक्ति में एक उत्तर चुनें।')
    .setRows([
      'Drinking water / पीने का पानी',
      'Shade / छाया',
      'Cool indoor space / ठंडी इनडोर जगह'
    ])
    .setColumns([
      'Always / हमेशा',
      'Often / अक्सर',
      'Sometimes / कभी-कभी',
      'Rarely / बहुत कम',
      'Never / कभी नहीं',
      'Do not know/not applicable / पता नहीं/लागू नहीं'
    ])
    .setRequired(true);

  addCheckboxQuestion(
    surveyForm,
    '7. Last summer (April–June 2026), did you experience any of these when it was hot? These are general experiences, not a diagnosis. / पिछली गर्मियों (अप्रैल–जून 2026) में गर्मी के दौरान क्या आपको इनमें से कुछ अनुभव हुआ? ये सामान्य अनुभव हैं, निदान नहीं।',
    [
      'Headache / सिरदर्द',
      'Dizziness or light-headedness / चक्कर या हल्कापन',
      'Unusual tiredness or weakness / असामान्य थकान या कमज़ोरी',
      'Muscle cramps / मांसपेशियों में ऐंठन',
      'Nausea / मितली',
      'Unusually heavy sweating / सामान्य से अधिक पसीना',
      'Feeling faint / बेहोशी जैसा लगना',
      'None of these / इनमें से कुछ नहीं',
      'Prefer not to answer / उत्तर नहीं देना चाहते'
    ],
    true,
    'If you choose “None” or “Prefer not to answer”, do not select another option. / “इनमें से कुछ नहीं” या “उत्तर नहीं देना चाहते” चुनें, तो कोई अन्य विकल्प न चुनें।'
  );

  surveyForm.addGridItem()
    .setTitle('8. During hot weather last summer (April–June 2026), how much did heat affect each activity? / पिछली गर्मियों (अप्रैल–जून 2026) के गर्म मौसम में गर्मी का हर गतिविधि पर कितना असर पड़ा?')
    .setHelpText('Choose one answer in each row. / हर पंक्ति में एक उत्तर चुनें।')
    .setRows([
      'Attending class / कक्षा में उपस्थिति',
      'Concentrating or studying / ध्यान लगाकर पढ़ाई',
      'Sleep / नींद',
      'Sport or physical activity / खेल या शारीरिक गतिविधि'
    ])
    .setColumns([
      'No effect / कोई असर नहीं',
      'A little / थोड़ा',
      'Some / कुछ',
      'A lot / बहुत',
      'Not applicable / लागू नहीं',
      'Prefer not to answer / उत्तर नहीं देना चाहते'
    ])
    .setRequired(true);

  addCheckboxQuestion(
    surveyForm,
    '9. What do you do now to cope with hot weather? Select all that apply. / गर्म मौसम से निपटने के लिए आप अभी क्या करते हैं? सभी लागू विकल्प चुनें।',
    [
      'Drink water / पानी पीना',
      'Seek shade / छाया ढूँढना',
      'Rest in a cooler place / ठंडी जगह पर आराम करना',
      'Change or avoid outdoor timings / बाहर जाने का समय बदलना या बाहर जाने से बचना',
      'Wear lighter clothing / हल्के कपड़े पहनना',
      'Use a fan or air-conditioning / पंखा या एयर-कंडीशनिंग इस्तेमाल करना',
      'Use an electrolyte drink/ORS / इलेक्ट्रोलाइट पेय/ORS लेना',
      'Take transport rather than walk / पैदल जाने के बजाय वाहन लेना',
      'No particular strategy / कोई विशेष तरीका नहीं',
      'Prefer not to say / बताना नहीं चाहते'
    ],
    true,
    'If you choose “No particular strategy” or “Prefer not to say”, do not select another option. / “कोई विशेष तरीका नहीं” या “बताना नहीं चाहते” चुनें, तो कोई अन्य विकल्प न चुनें।'
  );

  addCheckboxQuestion(
    surveyForm,
    '10. Where do you get weather/heat information, and how do you use heat alerts? Select all that apply. / मौसम/गर्मी की जानकारी आपको कहाँ से मिलती है और आप गर्मी के अलर्ट का कैसे उपयोग करते हैं? सभी लागू विकल्प चुनें।',
    [
      'Weather app or website / मौसम ऐप या वेबसाइट',
      'India Meteorological Department (IMD) / भारत मौसम विज्ञान विभाग (IMD)',
      'TV, radio or newspaper / टीवी, रेडियो या अख़बार',
      'Social media or messaging groups / सोशल मीडिया या मैसेजिंग समूह',
      'College notice or staff / कॉलेज सूचना या कर्मचारी',
      'Friends or family / मित्र या परिवार',
      'I use/check heat alerts when available / उपलब्ध होने पर गर्मी के अलर्ट देखता/देखती हूँ',
      'I have seen alerts but do not use them / अलर्ट देखे हैं पर उपयोग नहीं करता/करती',
      'I do not use heat alerts / गर्मी के अलर्ट उपयोग नहीं करता/करती',
      'I do not regularly check weather/heat information / मौसम/गर्मी की जानकारी नियमित रूप से नहीं देखता/देखती'
    ],
    true,
    'Select all information sources that apply, but choose only one of the heat-alert-use options. / सभी लागू जानकारी-स्रोत चुनें, लेकिन गर्मी के अलर्ट के उपयोग वाला केवल एक विकल्प चुनें।'
  );

  addMultipleChoiceQuestion(
    surveyForm,
    '11. Would you follow a cooler route if it took extra time? / अगर ठंडा रास्ता अपनाने में अतिरिक्त समय लगे, तो क्या आप उसे चुनेंगे/चुनेंगी?',
    [
      'Yes, +10 minutes / हाँ, +10 मिनट',
      'Yes, +5 minutes / हाँ, +5 मिनट',
      'Yes, +3 minutes / हाँ, +3 मिनट',
      'Only +0 minutes / केवल +0 मिनट',
      'No / नहीं',
      'Not sure / निश्चित नहीं'
    ],
    true
  );

  addMultipleChoiceQuestion(
    surveyForm,
    '12. Would you be willing to share location with a heat-safety app for relevant guidance? / उपयोगी सलाह पाने के लिए क्या आप गर्मी-सुरक्षा ऐप से अपना स्थान साझा करने को तैयार होंगे/होंगी?',
    [
      'No / नहीं',
      'Only while using the app / केवल ऐप इस्तेमाल करते समय',
      'Approximate campus area only, not precise location / केवल परिसर का अनुमानित क्षेत्र, सटीक स्थान नहीं',
      'Only when I actively request a feature / केवल जब मैं स्वयं कोई सुविधा माँगूँ',
      'Not sure / निश्चित नहीं',
      'Prefer not to say / बताना नहीं चाहते'
    ],
    true
  );

  addCheckboxQuestion(
    surveyForm,
    '13. Is there any condition or personal factor that makes heat harder for you? Please do not name a diagnosis or medication. / क्या कोई स्वास्थ्य-स्थिति या निजी कारण है जिससे गर्मी आपके लिए कठिन हो जाती है? कृपया बीमारी या दवा का नाम न लिखें।',
    [
      'A long-term health condition / दीर्घकालिक स्वास्थ्य-स्थिति',
      'Medication that affects heat tolerance / गर्मी सहने की क्षमता पर असर डालने वाली दवा',
      'Disability or mobility-related factor / दिव्यांगता या चलने-फिरने से जुड़ा कारण',
      'Another factor; no details needed / कोई अन्य कारण; विवरण ज़रूरी नहीं',
      'None / कोई नहीं',
      'Prefer not to say / बताना नहीं चाहते'
    ],
    false,
    'If you choose “None” or “Prefer not to say”, do not select another option. / “कोई नहीं” या “बताना नहीं चाहते” चुनें, तो कोई अन्य विकल्प न चुनें।'
  );

  surveyForm.addParagraphTextItem()
    .setTitle('14. Name up to 3 places on or near your campus where you feel the heat most. Place names only; no GPS, home address, or personal details. / अपने परिसर में या उसके पास अधिक गर्मी महसूस होने वाली अधिकतम 3 जगहों के नाम लिखें। केवल जगहों के नाम; GPS, घर का पता या निजी जानकारी नहीं।')
    .setRequired(false);

  surveyForm.addPageBreakItem()
    .setTitle('Optional student pilot sign-up / वैकल्पिक विद्यार्थी पायलट साइन-अप')
    .setHelpText(
      'If you would like to hear about a student pilot, use this separate form: ' + signupForm.getPublishedUrl() +
      '\nYour contact details will not be linked to your survey answers. / विद्यार्थी पायलट के बारे में जानने के लिए यह अलग फ़ॉर्म भरें। आपकी संपर्क जानकारी सर्वेक्षण के उत्तरों से नहीं जोड़ी जाएगी।'
    );

  Logger.log('Survey respondent URL: ' + surveyForm.getPublishedUrl());
  Logger.log('Survey edit URL: ' + surveyForm.getEditUrl());
  Logger.log('Separate sign-up respondent URL: ' + signupForm.getPublishedUrl());
  Logger.log('Separate sign-up edit URL: ' + signupForm.getEditUrl());

  return {
    surveyRespondentUrl: surveyForm.getPublishedUrl(),
    surveyEditUrl: surveyForm.getEditUrl(),
    signupRespondentUrl: signupForm.getPublishedUrl(),
    signupEditUrl: signupForm.getEditUrl()
  };
}

function addMultipleChoiceQuestion(form, title, choices, required) {
  form.addMultipleChoiceItem()
    .setTitle(title)
    .setChoiceValues(choices)
    .setRequired(required);
}

function addCheckboxQuestion(form, title, choices, required, helpText) {
  const item = form.addCheckboxItem()
    .setTitle(title)
    .setChoiceValues(choices)
    .setRequired(required);
  if (helpText) {
    item.setHelpText(helpText);
  }
}
