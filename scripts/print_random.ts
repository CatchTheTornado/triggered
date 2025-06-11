interface TriggerData {
  trigger: boolean;
  reason: string;
}

interface ScriptContext {
  data: TriggerData;
  params: Record<string, any>;
  env: Record<string, string>;
}

export default function(context: ScriptContext) {
  console.log('🎲 Random Number Generator');
  console.log('------------------------');
  console.log(`Triggered: ${context.data.trigger}`);
  console.log(`Reason: ${context.data.reason}`);
  console.log('------------------------');
  console.log('Parameters:', JSON.stringify(context.params, null, 2));
  console.log('Environment:', JSON.stringify(context.env, null, 2));
  console.log('------------------------');
} 