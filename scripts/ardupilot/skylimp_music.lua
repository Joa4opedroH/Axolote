-- Script inicial para o bonus de musica no ArduPilot.
-- Copiar para o diretorio APM/scripts do cartao SD da controladora.
-- Garanta que SCR_ENABLE=1 e que a controladora tenha buzzer configurado.

local played = false

function update()
  if not played then
    notify:play_tune("MFT200L8 O4 C E G O5 C")
    played = true
  end
  return update, 1000
end

return update()
