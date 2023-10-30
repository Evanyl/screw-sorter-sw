from data_interface import DataInterface, ScrewQuery, ImagingSession, Fastener, Screw


def main():
  
  interface = DataInterface('main.db', 'data')
  s = ScrewQuery()
  # s.measurement_system = ['imperial', 'metric']
  # s.processing = []
  # s.head = ['socket', 'flat']
  # s.drive = ['hex']
  # s.direction = ['right']
  s.finish = ['steel']
  # s.length = ['10', '20']
  # s.diameter = ['2.5']
  # s.pitch = ['0.45', '0.50']
  # s.length_n = (0.01, 100)
  # s.pitch_n = (0.0001, 100)
  # s = Screw('data/raw/real/real_img_ses_v1.0_c0_2023_10_10_<time>_gk/real_screw_metric_m2.5_0.45_10_socket_hex_<uuid>')
  # print(s.length)
  # interface.add_imaging_session('data/raw/real/real_img_ses_v1.0_c0_2023_10_10_<time>_gk')
  # interface.add_processed_images('data/raw/real/real_img_ses_v1.0_c0_2023_10_10_<time>_gk')
  uuids, paths = interface.get_screw_images(s)
  print(uuids)
  print(paths)



if __name__ == "__main__":
  main()