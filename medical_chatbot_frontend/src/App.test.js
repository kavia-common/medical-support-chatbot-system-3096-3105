import { render, screen } from '@testing-library/react';
import App from './App';

test('renders header brand title', () => {
  render(<App />);
  expect(screen.getByText(/CrewAI Medical Support/i)).toBeInTheDocument();
});
