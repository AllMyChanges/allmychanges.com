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

;; для автокомплита в js2-mode используем tern
;; https://truongtx.me/2014/04/20/emacs-javascript-completion-and-refactoring/
(setq tern-command (list (expand-file-name "node_modules/.bin/tern")))

(add-hook 'js-mode-hook (lambda () (tern-mode t)))

(eval-after-load 'tern
  '(progn
     (require 'tern-auto-complete)
     (tern-ac-setup)))

(require 'auto-complete)
(auto-complete-mode)
