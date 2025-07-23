import { ComponentFixture, TestBed } from '@angular/core/testing';

import { DashboardAppointments } from './dashboard-appointments';

describe('DashboardAppointments', () => {
  let component: DashboardAppointments;
  let fixture: ComponentFixture<DashboardAppointments>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [DashboardAppointments]
    })
    .compileComponents();

    fixture = TestBed.createComponent(DashboardAppointments);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
