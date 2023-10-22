from data_interface import DataInterface
from imaging_session import ImagingSession
from fastener import Screw


def main():
  
  interface = DataInterface('', 'data')
  s = Screw('data/raw/real/real_img_ses_v1.0_c0_2023_10_10_<time>_gk/real_screw_metric_m2.5_0.45_10_socket_hex_<uuid>')
  print(s.length)
  interface.add_imaging_session('data/raw/real/real_img_ses_v1.0_c0_2023_10_10_<time>_gk')


if __name__ == "__main__":
  main()