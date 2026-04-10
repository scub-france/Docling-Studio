function fn() {
  var config = {
    baseUrl: karate.properties['baseUrl'] || 'http://localhost:8000',
    pollInterval: 2000,
    pollTimeout: 120000,
    batchPollTimeout: 300000
  };
  karate.configure('connectTimeout', 10000);
  karate.configure('readTimeout', 30000);
  karate.configure('retry', { count: 60, interval: config.pollInterval });
  return config;
}
