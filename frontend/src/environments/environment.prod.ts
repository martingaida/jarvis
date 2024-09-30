export const environment = {
    production: true,
    s3Upload: process.env['S3_UPLOAD'],
    s3Transcript: process.env['S3_TRANSCRIPT'],
    mockDepositionUrl: process.env['MOCK_DEPOSITION_URL'],
    apiUrl: process.env['API_URL']
  };