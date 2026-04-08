function fn() {
  var config = {
    baseUrl: karate.properties['baseUrl'] || 'http://localhost:8000',
    uiBaseUrl: karate.properties['uiBaseUrl'] || 'http://localhost:3000',
    pollInterval: 2000,
    pollTimeout: 120000,
    batchPollTimeout: 300000
  };
  karate.configure('connectTimeout', 10000);
  karate.configure('readTimeout', 30000);
  karate.configure('retry', { count: 60, interval: config.pollInterval });

  // Karate UI — browser driver config (Chrome headless)
  karate.configure('driver', {
    type: 'chrome',
    headless: true,
    showDriverLog: false,
    addOptions: ['--no-sandbox', '--disable-gpu'],
    screenshotOnFailure: true
  });

  return config;
}
