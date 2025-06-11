interface TriggerData {
  number: number;
  message: string;
}

export default function(triggerData: TriggerData) {
  console.log('🎲 Random Number Generator');
  console.log('------------------------');
  console.log(`Number: ${triggerData.number}`);
  console.log(`Message: ${triggerData.message}`);
  console.log('------------------------');
} 