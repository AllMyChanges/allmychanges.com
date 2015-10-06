;; настройки для
;; https://github.com/areina/helm-dash
;; eww это браузер, встроенный в emacs 24.4
;; так же нужно apt-get install sqlite

(setq helm-dash-browser-func 'eww)
(setq helm-dash-docsets '("Python 2"))

;; активируем projectile и helm для него
(projectile-global-mode)
(setq projectile-completion-system 'helm)
(setq projectile-globally-ignored-directories '(".git" ".tox" "env" "node_modules"))
(helm-projectile-on)
