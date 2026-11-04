export type Message = string

declare module 'claude-code' {
  interface PluginState {
    zayana: { msg: Message; isHidden: boolean }
  }
}
