declare module 'prismjs' {
  export function highlightAll(): void;
  export function highlight(text: string, grammar: any, language: string): string;
  
  const Prism: {
    highlightAll: () => void;
    highlight: (text: string, grammar: any, language: string) => string;
  };
  
  export default Prism;
}

