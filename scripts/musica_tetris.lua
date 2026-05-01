---@diagnostic disable: undefined-global
local function update()
    local music = "MFT160L8E.B9C9D.C9B9A.A9C9E.D9C9B.B9C9D.E.C.A.A"
    --MF:musica tocada em primeiro plano
    --T160:tempo da musica, 160 batidas por minuto
    --L8:compasso, 8 tempos por compasso
    --E.B9C9D.C9B9A.A9C9E.D9C9B.B9C9D.E.C.A.A:sequencia de notas, cada nota tem um nome (G, A, B, C, D, E, F)
    --(G:sol, A:la, B:si, C:dó, D:ré, E:mi, F:fá) e o numero indica a oitava data nota (0, 1, 2, etc). O simbolo "." indica que a nota deve ser tocada por um tempo mais curto, e oitavas mais altas tem um som mais agudo, enquanto oitavas mais baixas tem um som mais grave.

    notify:play_tune(music)

    gcs:send_text(6, "tocando musica tema tetris")
    --6 significa informativo 

    return update, 1000

end

return update(), 1000
