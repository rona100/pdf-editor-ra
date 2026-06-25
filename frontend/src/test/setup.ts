import '@testing-library/jest-dom'

// jsdom doesn't implement these URL methods; define no-op stubs so tests can spy on them
if (typeof URL.createObjectURL === 'undefined') {
  URL.createObjectURL = () => 'blob:stub'
}
if (typeof URL.revokeObjectURL === 'undefined') {
  URL.revokeObjectURL = () => {}
}
