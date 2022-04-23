pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
moduledir = join_paths(pkgdatadir, 'badabib')
gnome = import('gnome')

gnome.compile_resources('badabib',
  'badabib.gresource.xml',
  gresource_bundle: true,
  install: true,
  install_dir: pkgdatadir,
)

python = import('python')

conf = configuration_data()
conf.set('PYTHON', python.find_installation('python3').path())
conf.set('VERSION', meson.project_version())
conf.set('localedir', join_paths(get_option('prefix'), get_option('localedir')))
conf.set('pkgdatadir', pkgdatadir)

configure_file(
  input: 'badabib.in',
  output: 'badabib',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir')
)

badabib_sources = [
  '__init__.py',
  'application.py',
  'window.py',
  'customization.py',
  'bibitem.py',
  'config_manager.py',
  'store.py',
  'forms.py',
  'change.py',
  'dialogs.py',
  'editor.py',
  'layout_manager.py',
  'itemlist.py',
  'main_widget.py',
  'default_layouts.py',
  'bibfile.py',
  'string_manager.py',
  'session_manager.py',
  'preferences.py',
  'watcher.py',
  'menus.py',
]

install_data(badabib_sources, install_dir: moduledir)
