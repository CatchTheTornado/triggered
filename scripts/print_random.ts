interface TriggerData {
  number: number;
  message: string;
}

// The trigger data is passed as a global variable
declare const triggerData: TriggerData;

console.log('🎲 Random Number Generator');
console.log('------------------------');
console.log(`Number: ${triggerData.number}`);
console.log(`Message: ${triggerData.message}`);
console.log('------------------------'); 