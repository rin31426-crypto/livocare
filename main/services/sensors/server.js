const express = require('express');
const cors = require('cors');

const app = express();
const PORT = process.env.PORT || 3000;

// ========== إعدادات أساسية ==========
app.use(cors());
app.use(express.json());

// ========== تخزين مؤقت للبيانات (في الذاكرة) ==========
// ملاحظة: هذه البيانات تختفي عند إعادة تشغيل الخدمة
// للاستخدام الدائم، ستحتاجين إلى قاعدة بيانات منفصلة
let readings = [];

// ========== استقبال بيانات من ESP32 ==========
app.post('/api/readings', (req, res) => {
  const { bpm, spo2 } = req.body;

  if (!bpm || !spo2) {
    return res.status(400).json({ 
      status: 'error', 
      message: 'البيانات ناقصة! يلزم إرسال bpm و spo2' 
    });
  }

  const newReading = {
    id: readings.length + 1,
    bpm: bpm,
    spo2: spo2,
    timestamp: new Date().toISOString()
  };

  readings.push(newReading);
  
  // الاحتفاظ بآخر 1000 قراءة فقط لتوفير المساحة
  if (readings.length > 1000) {
    readings = readings.slice(-1000);
  }

  console.log(`📊 [${newReading.timestamp}] BPM: ${bpm}, SpO2: ${spo2}%`);
  console.log(`📦 إجمالي القراءات المخزنة: ${readings.length}`);

  res.status(200).json({ 
    status: 'success', 
    message: 'تم استلام البيانات بنجاح!',
    id: newReading.id
  });
});

// ========== استرجاع آخر القراءات (للواجهة الأمامية) ==========
app.get('/api/readings/latest', (req, res) => {
  if (readings.length === 0) {
    return res.status(200).json({ 
      status: 'success', 
      data: null,
      message: 'لا توجد قراءات بعد' 
    });
  }
  
  const latest = readings[readings.length - 1];
  res.status(200).json({ 
    status: 'success', 
    data: latest 
  });
});

// ========== استرجاع جميع القراءات (للواجهة الأمامية) ==========
app.get('/api/readings/all', (req, res) => {
  res.status(200).json({ 
    status: 'success', 
    count: readings.length,
    data: readings 
  });
});

// ========== نقطة صحية للتحقق من عمل الخدمة ==========
app.get('/health', (req, res) => {
  res.status(200).json({ 
    status: 'ok', 
    message: 'LivoCare API is running!',
    totalReadings: readings.length
  });
});

// ========== تشغيل الخادم ==========
app.listen(PORT, () => {
  console.log(`✅ LivoCare API يعمل على المنفذ ${PORT}`);
  console.log(`📍 المسارات المتاحة:`);
  console.log(`   POST /api/readings - لإرسال بيانات جديدة`);
  console.log(`   GET  /api/readings/latest - لآخر قراءة`);
  console.log(`   GET  /api/readings/all - لجميع القراءات`);
  console.log(`   GET  /health - للتحقق من الحالة`);
});