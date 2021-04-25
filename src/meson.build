kooha_sources += [
  'main.vala',
  'window.vala',
]

kooha_deps = [
  dependency('gio-2.0', version: '>= 2.50'),
  dependency('gtk+-3.0', version: '>= 3.22'),
  dependency('libhandy-1', version: '>= 1.0.3'),
]

gnome = import('gnome')

executable('kooha', kooha_sources,
  vala_args: '--target-glib=2.50',
  dependencies: kooha_deps,
  install: true,
)
